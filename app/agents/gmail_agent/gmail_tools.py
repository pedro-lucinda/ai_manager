"""Gmail toolkit integration with env-based OAuth credentials."""

from __future__ import annotations

import os
from functools import lru_cache
from typing import TYPE_CHECKING, List

from google_auth_oauthlib.flow import InstalledAppFlow
from langchain_core.tools import BaseTool
from langchain_google_community import GmailToolkit
from langchain_google_community.gmail.utils import build_gmail_service

if TYPE_CHECKING:
    from google.oauth2.credentials import Credentials

DEFAULT_SCOPES = ["https://mail.google.com/"]
DEFAULT_TOKEN_FILE = "token.json"
DEFAULT_OAUTH_PORT = 8080


def _get_required_env(name: str) -> str:
    value = os.environ.get(name)
    if not value:
        raise ValueError(
            f"Missing required environment variable: {name}. "
            "Set GMAIL_CLIENT_ID and GMAIL_CLIENT_SECRET before using Gmail tools."
        )
    return value


def _get_scopes() -> List[str]:
    scopes = os.environ.get("GMAIL_SCOPES")
    if not scopes:
        return DEFAULT_SCOPES
    return [scope.strip() for scope in scopes.split(",") if scope.strip()]


def _get_token_file() -> str:
    return os.environ.get("GMAIL_TOKEN_FILE", DEFAULT_TOKEN_FILE)


def _get_oauth_port() -> int:
    port = int(os.environ.get("GMAIL_OAUTH_PORT", DEFAULT_OAUTH_PORT))
    if port <= 0:
        raise ValueError("GMAIL_OAUTH_PORT must be a positive integer.")
    return port


def _get_redirect_uri() -> str:
    return f"http://localhost:{_get_oauth_port()}/"


def _build_client_config() -> dict:
    return {
        "installed": {
            "client_id": _get_required_env("GMAIL_CLIENT_ID"),
            "client_secret": _get_required_env("GMAIL_CLIENT_SECRET"),
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
            "redirect_uris": [_get_redirect_uri()],
        }
    }


def _get_credentials() -> Credentials:
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials

    scopes = _get_scopes()
    token_file = _get_token_file()
    creds: Credentials | None = None

    if os.path.exists(token_file):
        creds = Credentials.from_authorized_user_file(token_file, scopes)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_config(
                _build_client_config(),
                scopes,
            )
            creds = flow.run_local_server(port=_get_oauth_port())

        with open(token_file, "w") as token:
            token.write(creds.to_json())

    return creds


@lru_cache(maxsize=1)
def get_gmail_tools() -> List[BaseTool]:
    """Return Gmail toolkit tools, initializing OAuth credentials on first call."""
    api_resource = build_gmail_service(credentials=_get_credentials())
    toolkit = GmailToolkit(api_resource=api_resource)
    return toolkit.get_tools()


def __getattr__(name: str):
    if name == "tools":
        return get_gmail_tools()
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
