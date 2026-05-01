from fastapi import FastAPI, File, UploadFile
from pydantic import BaseModel

from config import settings
from storage import FileStorage, FileValidator

app = FastAPI(title="aivm-photo-api", version="0.1.0")

_validator = FileValidator(settings)
_storage = FileStorage(settings)


class UploadResponse(BaseModel):
    filename: str
    size_bytes: int
    content_type: str


@app.get("/health", tags=["ops"])
async def health() -> dict:
    return {"status": "ok"}


@app.post(
    "/images/upload",
    response_model=UploadResponse,
    status_code=201,
    tags=["images"],
)
async def upload_image(file: UploadFile = File(...)) -> UploadResponse:
    content = await file.read()
    _validator.validate(file, content)
    content_type = file.content_type or ""
    filename = _storage.save(content, content_type)
    return UploadResponse(
        filename=filename,
        size_bytes=len(content),
        content_type=content_type,
    )
