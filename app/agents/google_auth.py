"""Shared Google OAuth credential builder for Gmail and Calendar toolkits."""

from __future__ import annotations

import os
import secrets
from dataclasses import dataclass
from typing import TYPE_CHECKING

from google_auth_oauthlib.flow import Flow

from app.config import get_settings

if TYPE_CHECKING:
    from google.oauth2.credentials import Credentials


class GoogleAuthRequiredError(Exception):
    """Raised when Google credentials are missing or invalid."""

    def __init__(self, service: str) -> None:
        self.service = service
        super().__init__(f"{service} authorization required.")


@dataclass(frozen=True)
class PendingOAuth:
    service: str
    scopes: list[str]
    token_file: str
    redirect_uri: str


_pending_oauth: dict[str, PendingOAuth] = {}


def _client_config(client_id: str, client_secret: str, redirect_uri: str) -> dict:
    return {
        "web": {
            "client_id": client_id,
            "client_secret": client_secret,
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "redirect_uris": [redirect_uri],
        }
    }


def create_oauth_flow(scopes: list[str], redirect_uri: str) -> Flow:
    settings = get_settings()
    return Flow.from_client_config(
        _client_config(
            settings.gmail_client_id,
            settings.gmail_client_secret,
            redirect_uri,
        ),
        scopes=scopes,
        redirect_uri=redirect_uri,
    )


def start_oauth_flow(
    *,
    service: str,
    scopes: list[str],
    token_file: str,
    redirect_uri: str,
) -> str:
    """Return the Google authorization URL and store pending OAuth state."""
    flow = create_oauth_flow(scopes, redirect_uri)
    state = secrets.token_urlsafe(32)
    authorization_url, _ = flow.authorization_url(
        access_type="offline",
        include_granted_scopes="true",
        prompt="consent",
        state=state,
    )
    _pending_oauth[state] = PendingOAuth(
        service=service,
        scopes=scopes,
        token_file=token_file,
        redirect_uri=redirect_uri,
    )
    return authorization_url


def complete_oauth_flow(state: str, code: str) -> str:
    """Exchange an authorization code for credentials and return the service name."""
    pending = _pending_oauth.pop(state, None)
    if pending is None:
        raise ValueError("Invalid or expired OAuth state.")

    flow = create_oauth_flow(pending.scopes, pending.redirect_uri)
    flow.fetch_token(code=code)
    save_credentials(flow.credentials, pending.token_file)
    return pending.service


def save_credentials(credentials: Credentials, token_file: str) -> None:
    with open(token_file, "w") as token:
        token.write(credentials.to_json())


def try_load_credentials(scopes: list[str], token_file: str) -> Credentials | None:
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials

    if not os.path.exists(token_file):
        return None

    creds = Credentials.from_authorized_user_file(token_file, scopes)
    if creds and creds.valid:
        return creds

    if creds and creds.expired and creds.refresh_token:
        try:
            creds.refresh(Request())
            save_credentials(creds, token_file)
            return creds
        except Exception:
            return None

    return None


def is_authorized(scopes: list[str], token_file: str) -> bool:
    creds = try_load_credentials(scopes, token_file)
    return creds is not None and creds.valid


def build_google_credentials(
    scopes: list[str],
    token_file: str,
    *,
    service: str = "google",
) -> Credentials:
    """Load Google OAuth credentials, raising if authorization is required."""
    creds = try_load_credentials(scopes, token_file)
    if creds is None or not creds.valid:
        raise GoogleAuthRequiredError(service)
    return creds
