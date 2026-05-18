"""Export FastAPI OpenAPI spec to openapi.json, injecting OcrMeta schemas."""
import json
import sys
import os

os.environ.setdefault("API_TOKEN", "placeholder")
os.environ.setdefault("STORAGE_PATH", "/data/photos")

from app.main import app
from app.schemas import OcrMeta

def inject_pydantic_model(spec: dict, model_class) -> None:
    """Add Pydantic model + its $defs into components/schemas, fixing $ref paths."""
    schema = model_class.model_json_schema()

    # Hoist nested $defs into top-level components
    if "$defs" in schema:
        for name, def_schema in schema.pop("$defs").items():
            spec["components"]["schemas"][name] = def_schema

    # Rewrite local refs to global component refs
    schema_str = json.dumps(schema).replace('"#/$defs/', '"#/components/schemas/')
    spec["components"]["schemas"][model_class.__name__] = json.loads(schema_str)

spec = app.openapi()

# Inject OcrMeta (and its nested OcrInferenceMs, OcrConfidence)
inject_pydantic_model(spec, OcrMeta)

# Update the upload endpoint's form body to reference OcrMeta for ocr_meta field
upload_body = spec["components"]["schemas"].get("Body_upload_image_images_upload_post", {})
if "properties" in upload_body:
    upload_body["properties"]["ocr_meta"] = {
        "anyOf": [{"$ref": "#/components/schemas/OcrMeta"}, {"type": "null"}],
        "title": "Ocr Meta",
    }

out = sys.argv[1] if len(sys.argv) > 1 else "openapi.json"
with open(out, "w", encoding="utf-8") as f:
    json.dump(spec, f, indent=2)
print(f"OpenAPI spec written to {out}")
