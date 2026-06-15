from fastapi import FastAPI

from app.config import get_settings
from app.routers import assistant_chat, health

get_settings()

app = FastAPI(title="Manager")

app.include_router(health.router)
app.include_router(assistant_chat.router)
