import os
from typing import FrozenSet


class Settings:
    """Application settings resolved from environment variables at startup."""

    def __init__(self) -> None:
        self.storage_path: str = os.getenv("STORAGE_PATH", "/mnt/dataset")
        self.max_file_size_mb: int = int(os.getenv("MAX_FILE_SIZE_MB", "50"))
        self.allowed_content_types: FrozenSet[str] = frozenset({
            "image/jpeg",
            "image/png",
            "image/gif",
            "image/webp",
            "image/bmp",
            "image/tiff",
        })

    @property
    def max_file_size_bytes(self) -> int:
        return self.max_file_size_mb * 1024 * 1024


settings = Settings()
