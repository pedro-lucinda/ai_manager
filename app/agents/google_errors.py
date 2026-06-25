"""Google OAuth and API error message mapping."""

from __future__ import annotations

from google_auth_oauthlib.flow import WSGITimeoutError


def google_error_detail(exc: Exception) -> str | None:
    """Return a user-facing detail string for known Google errors, or None."""
    messages: list[str] = []
    current: BaseException | None = exc
    while current is not None:
        messages.append(str(current).lower())
        current = current.__cause__

    combined = " ".join(messages)

    if isinstance(exc, WSGITimeoutError):
        return (
            "Google authorization timed out. Check the server logs for the OAuth URL, "
            "complete sign-in in your browser, then retry."
        )
    if isinstance(exc, OSError) and (
        exc.errno == 48 or "address already in use" in combined
    ):
        return (
            "Google OAuth port is already in use. Set GMAIL_OAUTH_PORT to a free port "
            "and register the matching redirect URI in Google Cloud Console."
        )
    if "redirect_uri_mismatch" in combined:
        return (
            "Google OAuth redirect URI mismatch. Add "
            "http://127.0.0.1:8000/auth/gmail/callback and "
            "http://127.0.0.1:8000/auth/calendar/callback "
            "to your OAuth client's authorized redirect URIs in Google Cloud Console."
        )
    if (
        "accessnotconfigured" in combined
        or "calendar api has not been used" in combined
        or "calendar-json.googleapis.com" in combined
    ):
        return (
            "Google Calendar API is not enabled for this project. Enable it at "
            "https://console.cloud.google.com/apis/library/calendar-json.googleapis.com "
            "then wait a few minutes and retry."
        )
    return None
