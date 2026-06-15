from functools import lru_cache

from langchain.agents import create_agent

from app.agents.gmail_agent.gmail_tools import get_gmail_tools
from app.agents.gmail_agent.llm import llm
from app.agents.gmail_agent.prompt import SYSTEM_PROMPT


@lru_cache(maxsize=1)
def get_gmail_agent():
    return create_agent(
        model=llm,
        tools=get_gmail_tools(),
        system_prompt=SYSTEM_PROMPT,
    )
