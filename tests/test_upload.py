import json
import os
import pytest
from fastapi.testclient import TestClient

os.environ["API_TOKEN"] = "test-token"
os.environ["STORAGE_PATH"] = "/tmp/test-photos"

from app.main import app
from app.config import settings

client = TestClient(app)

AUTH = {"Authorization": "Bearer test-token"}

BASE_FIELDS = {
    "sys": "120",
    "dia": "80",
    "pul": "70",
    "timestamp": "2026-05-02T10:00:00+03:00",
    "source": "manual",
    "corrected_by_user": "false",
}

def _upload(data: dict, filename="test.jpg", content_type="image/jpeg", content=b"fake-image-content", headers=AUTH):
    return client.post(
        "/images/upload",
        headers=headers,
        data=data,
        files={"file": (filename, content, content_type)},
    )

def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}

def test_upload_no_auth():
    response = client.post("/images/upload")
    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid or missing token"

def test_upload_wrong_token():
    response = _upload(BASE_FIELDS, headers={"Authorization": "Bearer wrong-token"})
    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid or missing token"

def test_upload_success(temp_storage):
    response = _upload(BASE_FIELDS)
    assert response.status_code == 201
    data = response.json()
    assert data["filename"] == "20260502_100000.jpg"
    assert data["folder"] == "2026-05"
    assert (temp_storage / "2026-05" / "20260502_100000.jpg").exists()
    assert (temp_storage / "2026-05" / "20260502_100000.json").exists()

def test_upload_with_ai_suggested(temp_storage):
    fields = {**BASE_FIELDS, "ai_suggested_sys": "118", "ai_suggested_dia": "78", "ai_suggested_pul": "68"}
    response = _upload(fields)
    assert response.status_code == 201

def test_upload_missing_required_field():
    fields = {k: v for k, v in BASE_FIELDS.items() if k != "sys"}
    response = _upload(fields)
    assert response.status_code == 422

def test_upload_invalid_metadata_range():
    fields = {**BASE_FIELDS, "sys": "999"}
    response = _upload(fields)
    assert response.status_code == 422

def test_upload_unsupported_media_type():
    fields = {**BASE_FIELDS, "timestamp": "2026-05-02T11:00:00+03:00"}
    response = _upload(fields, filename="test.txt", content_type="text/plain")
    assert response.status_code == 415

def test_upload_collision(temp_storage):
    response1 = _upload(BASE_FIELDS)
    assert response1.status_code == 201
    response2 = _upload(BASE_FIELDS)
    assert response2.status_code == 409
    assert response2.json()["detail"] == "photo for this timestamp already exists"

def test_upload_with_ocr_meta(temp_storage):
    ocr_meta = json.dumps({
        "engine": "local",
        "model_version": "int8_v1",
        "inference_ms": {"display": 120, "digits": 95, "postprocess": 5},
        "confidence": {"min": 0.71, "mean": 0.84},
        "fallback_reason": None,
        "user_agent": "Mozilla/5.0",
        "hw_concurrency": 8,
    })
    fields = {**BASE_FIELDS, "timestamp": "2026-05-02T14:00:00+03:00", "ocr_meta": ocr_meta}
    response = _upload(fields)
    assert response.status_code == 201

def test_upload_with_invalid_ocr_meta():
    fields = {**BASE_FIELDS, "ocr_meta": "not-valid-json"}
    response = _upload(fields)
    assert response.status_code == 422

def test_upload_file_too_large():
    settings.max_file_size_mb = 0
    fields = {**BASE_FIELDS, "timestamp": "2026-05-02T13:00:00+03:00"}
    response = _upload(fields, content=b"x" * 100)
    assert response.status_code == 413
    assert "exceeds" in response.json()["detail"]
    settings.max_file_size_mb = 50

@pytest.fixture
def temp_storage(tmp_path):
    settings.storage_path = str(tmp_path)
    return tmp_path
