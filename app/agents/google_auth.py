"""Shared Google OAuth credential builder for Gmail and Calendar toolkits."""

from __future__ import annotations

import os
from typing import TYPE_CHECKING, List

from google_auth_oauthlib.flow import InstalledAppFlow

if TYPE_CHECKING:
    from google.oauth2.credentials import Credentials

DEFAULT_OAUTH_PORT = 8080


def _get_required_env(name: str) -> str:
    value = os.environ.get(name)
    if not value:
        raise ValueError(
            f"Missing required environment variable: {name}. "
            "Set GMAIL_CLIENT_ID and GMAIL_CLIENT_SECRET before using Google tools."
        )
    return value


def _get_oauth_port(port: int | None = None) -> int:
    if port is not None:
        return port
    port_value = int(os.environ.get("GMAIL_OAUTH_PORT", DEFAULT_OAUTH_PORT))
    if port_value <= 0:
        raise ValueError("GMAIL_OAUTH_PORT must be a positive integer.")
    return port_value


def _get_redirect_uri(port: int) -> str:
    return f"http://localhost:{port}/"


def _build_client_config(port: int) -> dict:
    return {
        "installed": {
            "client_id": _get_required_env("GMAIL_CLIENT_ID"),
            "client_secret": _get_required_env("GMAIL_CLIENT_SECRET"),
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
            "redirect_uris": [_get_redirect_uri(port)],
        }
    }


def build_google_credentials(
    scopes: List[str],
    token_file: str,
    port: int | None = None,
) -> Credentials:
    """Load or obtain Google OAuth credentials for the given scopes and token file."""
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials

    oauth_port = _get_oauth_port(port)
    creds: Credentials | None = None

    if os.path.exists(token_file):
        creds = Credentials.from_authorized_user_file(token_file, scopes)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_config(
                _build_client_config(oauth_port),
                scopes,
            )
            creds = flow.run_local_server(port=oauth_port)

        with open(token_file, "w") as token:
            token.write(creds.to_json())

    return creds
