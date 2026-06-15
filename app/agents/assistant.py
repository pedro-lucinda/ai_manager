from functools import lru_cache

from langchain.agents import create_agent
from langchain_openai import ChatOpenAI

from app.agents.calendar.calendar_tools import get_calendar_mcp
from app.agents.gmail.gmail_tools import get_gmail_mcp
from app.agents.prompts import SYSTEM_PROMPT
from app.config import get_settings


@lru_cache(maxsize=1)
def get_llm() -> ChatOpenAI:
    settings = get_settings()
    return ChatOpenAI(
        model=settings.openai_model,
        temperature=settings.openai_temperature,
        max_retries=settings.openai_max_retries,
        api_key=settings.openai_api_key,
    )


@lru_cache(maxsize=1)
def get_assistant_agent():
    return create_agent(
        model=get_llm(),
        tools=get_gmail_mcp() + get_calendar_mcp(),
        system_prompt=SYSTEM_PROMPT,
    )
