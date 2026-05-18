from datetime import datetime
from typing import Literal
from pydantic import BaseModel, Field, field_validator

class HealthResponse(BaseModel):
    status: str

class OcrInferenceMs(BaseModel):
    display: int
    digits: int
    postprocess: int

class OcrConfidence(BaseModel):
    min: float
    mean: float

class OcrMeta(BaseModel):
    engine: Literal["local", "gemini", "manual"]
    model_version: str | None = None
    inference_ms: OcrInferenceMs | None = None
    confidence: OcrConfidence | None = None
    fallback_reason: Literal["low_confidence", "no_display", "wrong_row_count", "user_requested"] | None = None
    user_agent: str | None = None
    hw_concurrency: int | None = None

class UploadResponse(BaseModel):
    filename: str
    folder: str
    size_bytes: int

class RecognizeResponse(BaseModel):
    sys: int
    dia: int
    pul: int
    confidence: float
    elapsed_ms: int

class AISuggestion(BaseModel):
    sys: int = Field(..., ge=50, le=300)
    dia: int = Field(..., ge=30, le=200)
    pul: int = Field(..., ge=30, le=250)

class PhotoMetadata(BaseModel):
    sys: int = Field(..., ge=50, le=300)
    dia: int = Field(..., ge=30, le=200)
    pul: int = Field(..., ge=30, le=250)
    timestamp: datetime
    device_model: str = "unknown"
    source: Literal["local_ocr", "gemini", "gemini_auto", "manual", "user_confirmed"]
    corrected_by_user: bool
    ai_suggested: AISuggestion | None = None
    notes: str | None = None
    ocr_meta: OcrMeta | None = None

    @field_validator("timestamp")
    @classmethod
    def timestamp_must_have_timezone(cls, v: datetime) -> datetime:
        if v.tzinfo is None:
            raise ValueError("Timestamp must have a timezone")
        return v
