from dotenv import load_dotenv

load_dotenv()

from fastapi import FastAPI

from app.routers import gmail_chat, health

app = FastAPI(title="Manager")

app.include_router(health.router)
app.include_router(gmail_chat.router)
