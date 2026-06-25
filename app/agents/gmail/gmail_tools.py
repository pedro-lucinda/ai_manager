"""Gmail toolkit integration with env-based OAuth credentials."""

from __future__ import annotations

from functools import lru_cache

from langchain_core.tools import BaseTool
from langchain_google_community import GmailToolkit
from langchain_google_community.gmail.utils import build_gmail_service

from app.agents.google_auth import build_google_credentials
from app.config import get_settings


@lru_cache(maxsize=1)
def get_gmail_mcp() -> list[BaseTool]:
    """Return Gmail toolkit tools, initializing OAuth credentials on first call."""
    settings = get_settings()
    credentials = build_google_credentials(
        scopes=settings.gmail_scopes,
        token_file=settings.gmail_token_file,
        service="gmail",
    )
    api_resource = build_gmail_service(credentials=credentials)
    toolkit = GmailToolkit(api_resource=api_resource)
    return toolkit.get_tools()
