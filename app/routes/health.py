from fastapi import APIRouter
from app.schemas import HealthResponse

router = APIRouter()

@router.get("/health", tags=["ops"], response_model=HealthResponse)
async def health() -> dict:
    return {"status": "ok"}
