from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter(prefix="/health", tags=["health"])


class HealthResponse(BaseModel):
    status: str


@router.get("/")
def health_check() -> HealthResponse:
    return HealthResponse(status="ok")
