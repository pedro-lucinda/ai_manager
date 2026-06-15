"""Timezone resolution and local datetime helpers."""

from __future__ import annotations

import logging
import os
from datetime import datetime
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

logger = logging.getLogger(__name__)


def validate_timezone(timezone: str) -> str:
    try:
        ZoneInfo(timezone)
    except ZoneInfoNotFoundError as exc:
        raise ValueError(f"Invalid timezone: {timezone}") from exc
    return timezone


def get_system_timezone() -> str:
    tz = datetime.now().astimezone().tzinfo
    if tz is not None and hasattr(tz, "key"):
        return tz.key
    raise ValueError("Could not determine system timezone.")


def resolve_timezone(request_timezone: str | None = None) -> str:
    if request_timezone:
        return validate_timezone(request_timezone)

    env_timezone = os.environ.get("USER_TIMEZONE")
    if env_timezone:
        return validate_timezone(env_timezone)

    try:
        return get_system_timezone()
    except ValueError:
        logger.debug("System timezone unavailable, trying Google Calendar.")

    try:
        from app.agents.calendar_agent.calendar_tools import get_calendar_timezone

        return get_calendar_timezone()
    except Exception as exc:
        logger.warning("Failed to fetch Google Calendar timezone: %s", exc)
        raise ValueError(
            "Could not determine timezone. Set USER_TIMEZONE env var or pass "
            "timezone in the request body."
        ) from exc


def get_local_datetime(timezone: str) -> str:
    return datetime.now(ZoneInfo(timezone)).strftime("%Y-%m-%d %H:%M:%S")
