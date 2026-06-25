"""Clear cached tool and agent instances after OAuth changes."""


def clear_tool_caches() -> None:
    from app.agents.assistant import get_assistant_agent
    from app.agents.calendar.calendar_tools import get_calendar_mcp
    from app.agents.gmail.gmail_tools import get_gmail_mcp

    get_gmail_mcp.cache_clear()
    get_calendar_mcp.cache_clear()
    get_assistant_agent.cache_clear()
