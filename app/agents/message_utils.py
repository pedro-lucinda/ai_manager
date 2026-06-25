"""Helpers for extracting displayable data from LangChain agent messages."""

from __future__ import annotations

import json
from typing import Any

from langchain_core.messages import AIMessage, ToolMessage

MAX_TOOL_RESULT_LENGTH = 4_000


def _normalize_content(content: Any) -> str:
    if isinstance(content, str):
        return content
    return json.dumps(content, indent=2, default=str)


def _truncate(text: str, limit: int = MAX_TOOL_RESULT_LENGTH) -> str:
    if len(text) <= limit:
        return text
    return f"{text[:limit]}\n… (truncated)"


def extract_tool_calls(messages: list[Any]) -> list[dict[str, Any]]:
    """Return tool calls from agent messages with optional results."""
    pending_calls: list[dict[str, Any]] = []
    results_by_id: dict[str, str] = {}

    for message in messages:
        if isinstance(message, ToolMessage):
            results_by_id[message.tool_call_id] = _truncate(
                _normalize_content(message.content),
            )
            continue

        if not isinstance(message, AIMessage) or not message.tool_calls:
            continue

        for call in message.tool_calls:
            pending_calls.append(
                {
                    "name": call["name"],
                    "args": call.get("args") or {},
                    "id": call.get("id"),
                }
            )

    tool_calls: list[dict[str, Any]] = []
    for call in pending_calls:
        entry: dict[str, Any] = {
            "name": call["name"],
            "args": call["args"],
        }
        call_id = call.get("id")
        if call_id and call_id in results_by_id:
            entry["result"] = results_by_id[call_id]
        tool_calls.append(entry)

    return tool_calls
