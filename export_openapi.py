"""Export FastAPI OpenAPI spec to openapi.json."""
import json
import sys
import os

os.environ.setdefault("API_TOKEN", "placeholder")
os.environ.setdefault("STORAGE_PATH", "/data/photos")

from app.main import app

spec = app.openapi()
out = sys.argv[1] if len(sys.argv) > 1 else "openapi.json"
with open(out, "w", encoding="utf-8") as f:
    json.dump(spec, f, indent=2)
print(f"OpenAPI spec written to {out}")
