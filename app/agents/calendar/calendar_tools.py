"""Google Calendar toolkit integration with env-based OAuth credentials."""

from __future__ import annotations

from functools import lru_cache

from langchain_core.tools import BaseTool
from langchain_google_community import CalendarToolkit
from langchain_google_community.calendar.utils import build_calendar_service

from app.agents.calendar.search_events import PatchedCalendarSearchEvents
from app.agents.google_auth import build_google_credentials
from app.config import get_settings


@lru_cache(maxsize=1)
def get_calendar_mcp() -> list[BaseTool]:
    """Return Calendar toolkit tools, initializing OAuth credentials on first call."""
    settings = get_settings()
    credentials = build_google_credentials(
        scopes=settings.calendar_scopes,
        token_file=settings.calendar_token_file,
        service="calendar",
    )
    api_resource = build_calendar_service(credentials=credentials)
    toolkit = CalendarToolkit(api_resource=api_resource)
    tools = toolkit.get_tools()
    return _replace_search_events_tool(tools, api_resource)


def _replace_search_events_tool(
    tools: list[BaseTool], api_resource: object,
) -> list[BaseTool]:
    return [
        PatchedCalendarSearchEvents(api_resource=api_resource)
        if tool.name == "search_events"
        else tool
        for tool in tools
    ]
