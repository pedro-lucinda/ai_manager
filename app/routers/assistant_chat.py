import asyncio
import logging

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.agents.assistant import get_assistant_agent
from app.agents.google_errors import google_error_detail

logger = logging.getLogger(__name__)

router = APIRouter(tags=["assistant"])


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1)


class ChatResponse(BaseModel):
    reply: str


@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest) -> ChatResponse:
    if not request.message.strip():
        raise HTTPException(status_code=400, detail="Message cannot be empty.")

    try:
        agent = await asyncio.to_thread(get_assistant_agent)
        result = await agent.ainvoke({"messages": [("user", request.message)]})
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

    return ChatResponse(reply=reply)
