from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.config import get_settings
from app.routers import assistant_chat, auth, health

get_settings()

STATIC_DIR = Path(__file__).resolve().parent.parent / "static"

app = FastAPI(title="Manager")

app.include_router(health.router)
app.include_router(auth.router)
app.include_router(assistant_chat.router)

if STATIC_DIR.is_dir():
    app.mount("/", StaticFiles(directory=STATIC_DIR, html=True), name="static")
