import json
from fastapi import FastAPI, File, UploadFile, HTTPException, Depends, Form
from pydantic import BaseModel, ValidationError

from config import settings
from storage import FileStorage, FileValidator
from auth import require_token
from schemas import PhotoMetadata

app = FastAPI(title="aivm-photo-api", version="0.1.0")

_validator = FileValidator(settings)
_storage = FileStorage(settings)


class UploadResponse(BaseModel):
    filename: str
    folder: str
    size_bytes: int


@app.get("/health", tags=["ops"])
async def health() -> dict:
    return {"status": "ok"}


@app.post(
    "/images/upload",
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
