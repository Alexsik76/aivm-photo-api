from datetime import datetime
from typing import Literal, Optional
from fastapi import APIRouter, File, UploadFile, HTTPException, Depends, Form
from pydantic import ValidationError

from app.config import settings
from app.storage import FileStorage, FileValidator
from app.auth import require_token
from app.schemas import PhotoMetadata, AISuggestion, OcrMeta, UploadResponse

router = APIRouter()

_validator = FileValidator(settings)
_storage = FileStorage(settings)

@router.post(
    "/upload",
    response_model=UploadResponse,
    status_code=201,
    tags=["images"],
    dependencies=[Depends(require_token)],
)
async def upload_image(
    file: UploadFile = File(...),
    sys: int = Form(..., ge=50, le=300),
    dia: int = Form(..., ge=30, le=200),
    pul: int = Form(..., ge=30, le=250),
    timestamp: datetime = Form(...),
    source: Literal["local_ocr", "gemini", "gemini_auto", "manual", "user_confirmed"] = Form(...),
    corrected_by_user: bool = Form(...),
    device_model: Optional[str] = Form(None),
    ai_suggested_sys: Optional[int] = Form(None, ge=50, le=300),
    ai_suggested_dia: Optional[int] = Form(None, ge=30, le=200),
    ai_suggested_pul: Optional[int] = Form(None, ge=30, le=250),
    notes: Optional[str] = Form(None),
    ocr_meta: Optional[str] = Form(None),
) -> UploadResponse:
    try:
        ai_suggested = None
        if ai_suggested_sys is not None and ai_suggested_dia is not None and ai_suggested_pul is not None:
            ai_suggested = AISuggestion(sys=ai_suggested_sys, dia=ai_suggested_dia, pul=ai_suggested_pul)

        parsed_ocr_meta = None
        if ocr_meta:
            parsed_ocr_meta = OcrMeta.model_validate_json(ocr_meta)

        photo_metadata = PhotoMetadata(
            sys=sys,
            dia=dia,
            pul=pul,
            timestamp=timestamp,
            device_model=device_model or "unknown",
            source=source,
            corrected_by_user=corrected_by_user,
            ai_suggested=ai_suggested,
            notes=notes,
            ocr_meta=parsed_ocr_meta,
        )
    except (ValueError, ValidationError) as e:
        raise HTTPException(status_code=422, detail=str(e))

    content = await file.read()
    _validator.validate(file, content)

    folder, filename = _storage.save_with_metadata(
        content, file.content_type or "", photo_metadata
    )

    return UploadResponse(filename=filename, folder=folder, size_bytes=len(content))
