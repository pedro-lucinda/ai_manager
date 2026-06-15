"""Shared Google OAuth credential builder for Gmail and Calendar toolkits."""

from __future__ import annotations

import os
from typing import TYPE_CHECKING

from google_auth_oauthlib.flow import InstalledAppFlow

from app.config import get_settings

if TYPE_CHECKING:
    from google.oauth2.credentials import Credentials


def _redirect_uri(port: int) -> str:
    return f"http://localhost:{port}/"


def _client_config(client_id: str, client_secret: str, port: int) -> dict:
    return {
        "installed": {
            "client_id": client_id,
            "client_secret": client_secret,
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
            "redirect_uris": [_redirect_uri(port)],
        }
    }


def build_google_credentials(
    scopes: list[str],
    token_file: str,
    port: int | None = None,
) -> Credentials:
    """Load or obtain Google OAuth credentials for the given scopes and token file."""
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials

    settings = get_settings()
    oauth_port = port if port is not None else settings.oauth_port
    creds: Credentials | None = None

    if os.path.exists(token_file):
        creds = Credentials.from_authorized_user_file(token_file, scopes)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_config(
                _client_config(
                    settings.gmail_client_id,
                    settings.gmail_client_secret,
                    oauth_port,
                ),
                scopes,
            )
            creds = flow.run_local_server(port=oauth_port)

        with open(token_file, "w") as token:
            token.write(creds.to_json())

    return creds
