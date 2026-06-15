"""Google Calendar toolkit integration with env-based OAuth credentials."""

from __future__ import annotations

import os
from functools import lru_cache
from typing import List

from langchain_core.tools import BaseTool
from langchain_google_community import CalendarToolkit
from langchain_google_community.calendar.utils import build_calendar_service

from app.agents.google_auth import build_google_credentials

DEFAULT_SCOPES = ["https://www.googleapis.com/auth/calendar"]
DEFAULT_TOKEN_FILE = "token_calendar.json"


def _get_scopes() -> List[str]:
    scopes = os.environ.get("CALENDAR_SCOPES")
    if not scopes:
        return DEFAULT_SCOPES
    return [scope.strip() for scope in scopes.split(",") if scope.strip()]


def _get_token_file() -> str:
    return os.environ.get("CALENDAR_TOKEN_FILE", DEFAULT_TOKEN_FILE)


@lru_cache(maxsize=1)
def get_calendar_tools() -> List[BaseTool]:
    """Return Calendar toolkit tools, initializing OAuth credentials on first call."""
    credentials = build_google_credentials(
        scopes=_get_scopes(),
        token_file=_get_token_file(),
        port=None,
    )
    api_resource = build_calendar_service(credentials=credentials)
    toolkit = CalendarToolkit(api_resource=api_resource)
    tools = toolkit.get_tools()
    # Datetime is injected into the agent context per request; this tool is redundant
    # and adds an extra Calendar API call that can fail independently.
    return [tool for tool in tools if tool.name != "get_current_datetime"]


@lru_cache(maxsize=1)
def get_calendar_timezone() -> str:
    """Return the IANA timezone of the user's primary Google Calendar."""
    credentials = build_google_credentials(
        scopes=_get_scopes(),
        token_file=_get_token_file(),
        port=None,
    )
    api_resource = build_calendar_service(credentials=credentials)
    calendars = api_resource.calendarList().list().execute().get("items", [])
    if not calendars:
        raise ValueError("No calendars found.")

    for calendar in calendars:
        if calendar.get("primary"):
            return calendar["timeZone"]

    return calendars[0]["timeZone"]
