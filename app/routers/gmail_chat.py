import asyncio
import logging

from fastapi import APIRouter, HTTPException
from google_auth_oauthlib.flow import WSGITimeoutError
from pydantic import BaseModel, Field

from app.agents.gmail_agent.agent import get_gmail_agent

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/gmail", tags=["gmail"])


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1)


class ChatResponse(BaseModel):
    reply: str


def _oauth_error_detail(exc: Exception) -> str | None:
    message = str(exc).lower()
    if isinstance(exc, WSGITimeoutError):
        return (
            "Gmail authorization timed out. Check the server logs for the OAuth URL, "
            "complete sign-in in your browser, then retry."
        )
    if isinstance(exc, OSError) and (
        exc.errno == 48 or "address already in use" in message
    ):
        return (
            "Gmail OAuth port is already in use. Set GMAIL_OAUTH_PORT to a free port "
            "and register the matching redirect URI in Google Cloud Console."
        )
    if "redirect_uri_mismatch" in message:
        return (
            "Gmail OAuth redirect URI mismatch. Register http://localhost:8080/ "
            "(or your GMAIL_OAUTH_PORT value) in Google Cloud Console, or use a "
            "Desktop OAuth client."
        )
    return None


@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest) -> ChatResponse:
    if not request.message.strip():
        raise HTTPException(status_code=400, detail="Message cannot be empty.")

    try:
        agent = await asyncio.to_thread(get_gmail_agent)
        result = await agent.ainvoke({"messages": [("user", request.message)]})
    except ValueError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except Exception as exc:
        logger.exception("Gmail chat request failed")
        detail = _oauth_error_detail(exc)
        if detail is None:
            detail = "Failed to process Gmail chat request."
        raise HTTPException(status_code=503, detail=detail) from exc

    last_message = result["messages"][-1]
    reply = last_message.content
    if not isinstance(reply, str):
        reply = str(reply)

    if not reply.strip():
        raise HTTPException(
            status_code=500,
            detail="Gmail agent returned an empty response.",
        )

    return ChatResponse(reply=reply)
