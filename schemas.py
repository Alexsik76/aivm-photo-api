from datetime import datetime
from typing import Literal
from pydantic import BaseModel, Field, field_validator

class GeminiSuggestion(BaseModel):
    sys: int = Field(..., ge=50, le=300)
    dia: int = Field(..., ge=30, le=200)
    pul: int = Field(..., ge=30, le=250)

class PhotoMetadata(BaseModel):
    sys: int = Field(..., ge=50, le=300)
    dia: int = Field(..., ge=30, le=200)
    pul: int = Field(..., ge=30, le=250)
    timestamp: datetime
    device_model: str
    source: Literal["user_confirmed", "gemini_auto", "manual"]
    corrected_by_user: bool
    gemini_suggested: GeminiSuggestion | None = None
    notes: str | None = None
    quality_flags: dict | None = None

    @field_validator("timestamp")
    @classmethod
    def timestamp_must_have_timezone(cls, v: datetime) -> datetime:
        if v.tzinfo is None:
            raise ValueError("Timestamp must have a timezone")
        return v
