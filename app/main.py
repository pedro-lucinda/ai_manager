from dotenv import load_dotenv

load_dotenv()

from fastapi import FastAPI

from app.routers import assistant_chat, health

app = FastAPI(title="Manager")

app.include_router(health.router)
app.include_router(assistant_chat.router)
