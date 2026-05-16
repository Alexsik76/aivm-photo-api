import json
from fastapi import APIRouter, File, UploadFile, HTTPException, Depends, Form
from pydantic import BaseModel, ValidationError

from app.config import settings
from app.storage import FileStorage, FileValidator
from app.auth import require_token
from app.schemas import PhotoMetadata, UploadResponse

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
    metadata: str = Form(...),
) -> UploadResponse:
    # 1. Parse and validate metadata
    try:
        metadata_json = json.loads(metadata)
        photo_metadata = PhotoMetadata(**metadata_json)
    except (json.JSONDecodeError, ValidationError) as e:
        raise HTTPException(status_code=422, detail=str(e))

    # 2. Read and validate file
    content = await file.read()
    _validator.validate(file, content)
    
    # 3. Save
    folder, filename = _storage.save_with_metadata(
        content, file.content_type or "", photo_metadata
    )
    
    return UploadResponse(
        filename=filename,
        folder=folder,
        size_bytes=len(content),
    )
