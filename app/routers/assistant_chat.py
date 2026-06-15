import asyncio
import logging

from fastapi import APIRouter, HTTPException
from google_auth_oauthlib.flow import WSGITimeoutError
from pydantic import BaseModel, Field

from app.agents.assistant import get_assistant_agent
from app.agents.timezone import get_local_datetime, resolve_timezone

logger = logging.getLogger(__name__)

router = APIRouter(tags=["assistant"])


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1)
    timezone: str | None = Field(
        default=None,
        description="IANA timezone (e.g. America/Sao_Paulo). Defaults to USER_TIMEZONE env or system timezone.",
    )


class ChatResponse(BaseModel):
    reply: str


def _google_error_detail(exc: Exception) -> str | None:
    messages: list[str] = []
    current: BaseException | None = exc
    while current is not None:
        messages.append(str(current).lower())
        current = current.__cause__

    combined = " ".join(messages)

    if isinstance(exc, WSGITimeoutError):
        return (
            "Google authorization timed out. Check the server logs for the OAuth URL, "
            "complete sign-in in your browser, then retry."
        )
    if isinstance(exc, OSError) and (
        exc.errno == 48 or "address already in use" in combined
    ):
        return (
            "Google OAuth port is already in use. Set GMAIL_OAUTH_PORT to a free port "
            "and register the matching redirect URI in Google Cloud Console."
        )
    if "redirect_uri_mismatch" in combined:
        return (
            "Google OAuth redirect URI mismatch. Register http://localhost:8080/ "
            "(or your GMAIL_OAUTH_PORT value) in Google Cloud Console, or use a "
            "Desktop OAuth client."
        )
    if (
        "accessnotconfigured" in combined
        or "calendar api has not been used" in combined
        or "calendar-json.googleapis.com" in combined
    ):
        return (
            "Google Calendar API is not enabled for this project. Enable it at "
            "https://console.cloud.google.com/apis/library/calendar-json.googleapis.com "
            "then wait a few minutes and retry."
        )
    return None


@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest) -> ChatResponse:
    if not request.message.strip():
        raise HTTPException(status_code=400, detail="Message cannot be empty.")

    try:
        timezone = await asyncio.to_thread(resolve_timezone, request.timezone)
        local_datetime = get_local_datetime(timezone)
        agent = await asyncio.to_thread(get_assistant_agent, timezone)
        result = await agent.ainvoke(
            {
                "messages": [
                    (
                        "system",
                        f"Current local datetime in {timezone}: {local_datetime}",
                    ),
                    ("user", request.message),
                ]
            }
        )
    except ValueError as exc:
        if str(exc).startswith("Invalid timezone"):
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except Exception as exc:
        logger.exception("Assistant chat request failed")
        detail = _google_error_detail(exc)
        if detail is None:
            detail = "Failed to process chat request."
        raise HTTPException(status_code=503, detail=detail) from exc

    last_message = result["messages"][-1]
    reply = last_message.content
    if not isinstance(reply, str):
        reply = str(reply)

    if not reply.strip():
        raise HTTPException(
            status_code=500,
            detail="Assistant returned an empty response.",
        )

    return ChatResponse(reply=reply)
