import asyncio
import logging

from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.agents.assistant import get_assistant_agent
from app.agents.google_auth import GoogleAuthRequiredError
from app.agents.google_errors import google_error_detail
from app.agents.message_utils import extract_tool_calls
from app.routers.auth import auth_required_http_exception

logger = logging.getLogger(__name__)

router = APIRouter(tags=["assistant"])


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1)


class ToolCallResponse(BaseModel):
    name: str
    args: dict[str, Any]
    result: str | None = None


class ChatResponse(BaseModel):
    reply: str
    tool_calls: list[ToolCallResponse] = Field(default_factory=list)


@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest) -> ChatResponse:
    if not request.message.strip():
        raise HTTPException(status_code=400, detail="Message cannot be empty.")

    try:
        agent = await asyncio.to_thread(get_assistant_agent)
        result = await agent.ainvoke({"messages": [("user", request.message)]})
    except GoogleAuthRequiredError as exc:
        raise auth_required_http_exception(exc) from exc
    except ValueError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except Exception as exc:
        logger.exception("Assistant chat request failed")
        detail = google_error_detail(exc)
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

    tool_calls = [
        ToolCallResponse(**tool_call)
        for tool_call in extract_tool_calls(result["messages"])
    ]

    return ChatResponse(reply=reply, tool_calls=tool_calls)
