import logging
from urllib.parse import quote

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import RedirectResponse
from pydantic import BaseModel

from app.agents.google_auth import (
    GoogleAuthRequiredError,
    complete_oauth_flow,
    is_authorized,
    start_oauth_flow,
)
from app.agents.tool_cache import clear_tool_caches
from app.config import get_settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["auth"])


class ServiceAuthStatus(BaseModel):
    connected: bool


class AuthStatusResponse(BaseModel):
    gmail: ServiceAuthStatus
    calendar: ServiceAuthStatus


def _auth_status() -> AuthStatusResponse:
    settings = get_settings()
    return AuthStatusResponse(
        gmail=ServiceAuthStatus(
            connected=is_authorized(
                settings.gmail_scopes,
                settings.gmail_token_file,
            ),
        ),
        calendar=ServiceAuthStatus(
            connected=is_authorized(
                settings.calendar_scopes,
                settings.calendar_token_file,
            ),
        ),
    )


def _redirect_home(*, service: str, status: str, message: str | None = None) -> RedirectResponse:
    url = f"/?auth={service}&status={status}"
    if message:
        url = f"{url}&message={quote(message)}"
    return RedirectResponse(url=url, status_code=303)


@router.get("/status", response_model=AuthStatusResponse)
def auth_status() -> AuthStatusResponse:
    return _auth_status()


@router.get("/gmail/start")
def gmail_auth_start(request: Request) -> RedirectResponse:
    settings = get_settings()
    redirect_uri = str(request.url_for("gmail_auth_callback"))
    authorization_url = start_oauth_flow(
        service="gmail",
        scopes=settings.gmail_scopes,
        token_file=settings.gmail_token_file,
        redirect_uri=redirect_uri,
    )
    return RedirectResponse(url=authorization_url, status_code=303)


@router.get("/gmail/callback", name="gmail_auth_callback")
def gmail_auth_callback(
    request: Request,
    state: str | None = None,
    code: str | None = None,
    error: str | None = None,
) -> RedirectResponse:
    if error:
        return _redirect_home(service="gmail", status="error", message=error)
    if not state or not code:
        return _redirect_home(
            service="gmail",
            status="error",
            message="Missing authorization response from Google.",
        )

    try:
        service = complete_oauth_flow(state, code)
        clear_tool_caches()
        return _redirect_home(service=service, status="success")
    except Exception as exc:
        logger.exception("Gmail OAuth callback failed")
        return _redirect_home(service="gmail", status="error", message=str(exc))


@router.get("/calendar/start")
def calendar_auth_start(request: Request) -> RedirectResponse:
    settings = get_settings()
    redirect_uri = str(request.url_for("calendar_auth_callback"))
    authorization_url = start_oauth_flow(
        service="calendar",
        scopes=settings.calendar_scopes,
        token_file=settings.calendar_token_file,
        redirect_uri=redirect_uri,
    )
    return RedirectResponse(url=authorization_url, status_code=303)


@router.get("/calendar/callback", name="calendar_auth_callback")
def calendar_auth_callback(
    request: Request,
    state: str | None = None,
    code: str | None = None,
    error: str | None = None,
) -> RedirectResponse:
    if error:
        return _redirect_home(service="calendar", status="error", message=error)
    if not state or not code:
        return _redirect_home(
            service="calendar",
            status="error",
            message="Missing authorization response from Google.",
        )

    try:
        service = complete_oauth_flow(state, code)
        clear_tool_caches()
        return _redirect_home(service=service, status="success")
    except Exception as exc:
        logger.exception("Calendar OAuth callback failed")
        return _redirect_home(service="calendar", status="error", message=str(exc))


def auth_required_http_exception(exc: GoogleAuthRequiredError) -> HTTPException:
    return HTTPException(
        status_code=401,
        detail={
            "message": str(exc),
            "service": exc.service,
            "auth_url": f"/auth/{exc.service}/start",
        },
    )
