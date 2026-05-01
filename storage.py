import uuid
from pathlib import Path
from typing import FrozenSet

from fastapi import HTTPException, UploadFile

from config import Settings

_CONTENT_TYPE_EXTENSIONS: dict[str, str] = {
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/gif": ".gif",
    "image/webp": ".webp",
    "image/bmp": ".bmp",
    "image/tiff": ".tiff",
}


class FileValidator:
    """Validates uploaded files against configured constraints."""

    def __init__(self, settings: Settings) -> None:
        self._allowed: FrozenSet[str] = settings.allowed_content_types
        self._max_bytes: int = settings.max_file_size_bytes

    def validate(self, file: UploadFile, content: bytes) -> None:
        """Raise HTTPException if the file fails any validation check."""
        self._check_content_type(file.content_type or "")
        self._check_size(content)

    def _check_content_type(self, content_type: str) -> None:
        if content_type not in self._allowed:
            raise HTTPException(
                status_code=415,
                detail=f"Unsupported media type: '{content_type}'.",
            )

    def _check_size(self, content: bytes) -> None:
        if len(content) > self._max_bytes:
            max_mb = self._max_bytes // (1024 * 1024)
            raise HTTPException(
                status_code=413,
                detail=f"File size exceeds the {max_mb} MB limit.",
            )


class FileStorage:
    """Persists validated image files to disk."""

    def __init__(self, settings: Settings) -> None:
        self._base: Path = Path(settings.storage_path)
        self._base.mkdir(parents=True, exist_ok=True)

    def save(self, content: bytes, content_type: str) -> str:
        """Write *content* to disk and return the generated filename."""
        ext = _CONTENT_TYPE_EXTENSIONS.get(content_type, ".bin")
        filename = f"{uuid.uuid4().hex}{ext}"
        (self._base / filename).write_bytes(content)
        return filename
