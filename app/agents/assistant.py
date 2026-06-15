from functools import lru_cache

from langchain.agents import create_agent
from langchain_openai import ChatOpenAI

from app.agents.calendar_agent.calendar_tools import get_calendar_tools
from app.agents.gmail_agent.gmail_tools import get_gmail_tools

SYSTEM_PROMPT_TEMPLATE = """
You are a helpful assistant that can help with Gmail and Google Calendar tasks.

Gmail tasks:
- Send an email
- Reply to an email
- Forward an email
- Delete an email
- Search for an email
- Get the email thread
- Get the email details
- Get the email attachments

Google Calendar tasks:
- Create events
- Search events
- Update events
- Move events between calendars
- Delete events
- List events and calendar info

Scheduling rules (critical):
- The user's timezone is {timezone}.
- Times like "9am" or "tomorrow at 3pm" are in {timezone}, never UTC.
- Always pass timezone="{timezone}" when creating or updating calendar events.
- Use the current local datetime provided in the conversation context for scheduling.
"""

llm = ChatOpenAI(
    model="gpt-4o-mini",
    temperature=0,
    max_retries=2,
)


@lru_cache(maxsize=8)
def get_assistant_agent(timezone: str):
    return create_agent(
        model=llm,
        tools=get_gmail_tools() + get_calendar_tools(),
        system_prompt=SYSTEM_PROMPT_TEMPLATE.format(timezone=timezone),
    )
