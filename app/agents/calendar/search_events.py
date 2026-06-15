"""Patched calendar search_events tool — normalizes calendars_info input."""

from __future__ import annotations

import json
from typing import Any, Dict, List, Optional

from langchain_core.callbacks import CallbackManagerForToolRun
from langchain_google_community.calendar.search_events import CalendarSearchEvents


def normalize_calendars_data(calendars_info: str | list | dict) -> List[Dict[str, Any]]:
    """Parse calendars_info and always return a list of calendar dicts."""
    if isinstance(calendars_info, str):
        data = json.loads(calendars_info)
    else:
        data = calendars_info

    if isinstance(data, dict):
        return [data]
    if isinstance(data, list):
        return data

    raise ValueError(
        "calendars_info must be a JSON array of calendars from get_calendars_info."
    )


class PatchedCalendarSearchEvents(CalendarSearchEvents):
    """CalendarSearchEvents with calendars_info normalization."""

    def _run(
        self,
        calendars_info: str,
        min_datetime: str,
        max_datetime: str,
        max_results: int = 10,
        single_events: bool = True,
        order_by: str = "startTime",
        query: Optional[str] = None,
        run_manager: Optional[CallbackManagerForToolRun] = None,
    ) -> List[Dict[str, Optional[str]]]:
        calendars_data = normalize_calendars_data(calendars_info)
        return super()._run(
            calendars_info=json.dumps(calendars_data),
            min_datetime=min_datetime,
            max_datetime=max_datetime,
            max_results=max_results,
            single_events=single_events,
            order_by=order_by,
            query=query,
            run_manager=run_manager,
        )
