import json
import tempfile
from pathlib import Path
from typing import FrozenSet

from fastapi import HTTPException, UploadFile

from config import Settings
from schemas import PhotoMetadata

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
        self._settings = settings

    def validate(self, file: UploadFile, content: bytes) -> None:
        """Raise HTTPException if the file fails any validation check."""
        self._check_content_type(file.content_type or "")
        self._check_size(content)

    def _check_content_type(self, content_type: str) -> None:
        if content_type not in self._settings.allowed_content_types:
            raise HTTPException(
                status_code=415,
                detail=f"Unsupported media type: '{content_type}'.",
            )

    def _check_size(self, content: bytes) -> None:
        if len(content) > self._settings.max_file_size_bytes:
            max_mb = self._settings.max_file_size_bytes // (1024 * 1024)
            raise HTTPException(
                status_code=413,
                detail=f"File size exceeds the {max_mb} MB limit.",
            )


class FileStorage:
    """Persists validated image files and metadata to disk."""

    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    @property
    def _base(self) -> Path:
        return Path(self._settings.storage_path)

    def save_with_metadata(
        self, content: bytes, content_type: str, metadata: PhotoMetadata
    ) -> tuple[str, str]:
        """
        Write image and metadata to disk atomically.
        Returns (folder_name, filename).
        """
        # 1. Derive names
        ts = metadata.timestamp
        folder_name = ts.strftime("%Y-%m")
        base_name = ts.strftime("%Y%m%d_%H%M%S")
        ext = _CONTENT_TYPE_EXTENSIONS.get(content_type, ".bin")
        
        target_dir = self._base / folder_name
        target_dir.mkdir(parents=True, exist_ok=True)
        
        img_path = target_dir / f"{base_name}{ext}"
        json_path = target_dir / f"{base_name}.json"
        
        # 2. Collision handling
        if img_path.exists() or json_path.exists():
            raise HTTPException(
                status_code=409,
                detail="photo for this timestamp already exists",
            )
            
        # 3. Atomic write using temporary files in the same directory
        temp_img = None
        temp_json = None
        try:
            # We use suffix to keep the extension for some OS/tools if needed, 
            # but mainly to distinguish.
            with tempfile.NamedTemporaryFile(dir=target_dir, delete=False, suffix=".tmp") as f_img:
                f_img.write(content)
                temp_img = Path(f_img.name)
            
            with tempfile.NamedTemporaryFile(dir=target_dir, delete=False, suffix=".tmp") as f_json:
                f_json.write(metadata.model_dump_json(indent=2).encode("utf-8"))
                temp_json = Path(f_json.name)
            
            # Atomic rename
            temp_img.rename(img_path)
            temp_json.rename(json_path)
            
        except Exception as e:
            # Cleanup on failure
            if temp_img and temp_img.exists():
                temp_img.unlink()
            if temp_json and temp_json.exists():
                temp_json.unlink()
            # If renames happened partially, we might have orphan final files, 
            # but rename is usually atomic on the same filesystem.
            # To be safer, if img renamed but json failed:
            if img_path.exists() and not json_path.exists():
                img_path.unlink()
            
            raise HTTPException(status_code=500, detail=f"Storage error: {str(e)}")
            
        return folder_name, img_path.name
