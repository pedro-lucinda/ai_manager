"""Gmail toolkit integration with env-based OAuth credentials."""

from __future__ import annotations

import os
from functools import lru_cache
from typing import List

from langchain_core.tools import BaseTool
from langchain_google_community import GmailToolkit
from langchain_google_community.gmail.utils import build_gmail_service

from app.agents.google_auth import build_google_credentials

DEFAULT_SCOPES = ["https://mail.google.com/"]
DEFAULT_TOKEN_FILE = "token.json"


def _get_scopes() -> List[str]:
    scopes = os.environ.get("GMAIL_SCOPES")
    if not scopes:
        return DEFAULT_SCOPES
    return [scope.strip() for scope in scopes.split(",") if scope.strip()]


def _get_token_file() -> str:
    return os.environ.get("GMAIL_TOKEN_FILE", DEFAULT_TOKEN_FILE)


@lru_cache(maxsize=1)
def get_gmail_tools() -> List[BaseTool]:
    """Return Gmail toolkit tools, initializing OAuth credentials on first call."""
    credentials = build_google_credentials(
        scopes=_get_scopes(),
        token_file=_get_token_file(),
        port=None,
    )
    api_resource = build_gmail_service(credentials=credentials)
    toolkit = GmailToolkit(api_resource=api_resource)
    return toolkit.get_tools()


def __getattr__(name: str):
    if name == "tools":
        return get_gmail_tools()
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
