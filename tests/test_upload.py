import os
import json
import pytest
from fastapi.testclient import TestClient
from pathlib import Path

# Mock environment variables before importing app
os.environ["API_TOKEN"] = "test-token"
os.environ["STORAGE_PATH"] = "/tmp/test-photos"

from main import app, settings

client = TestClient(app)

@pytest.fixture
def temp_storage(tmp_path):
    settings.storage_path = str(tmp_path)
    return tmp_path

def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}

def test_upload_no_auth():
    response = client.post("/images/upload")
    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid or missing token"

def test_upload_wrong_token():
    response = client.post(
        "/images/upload",
        headers={"Authorization": "Bearer wrong-token"}
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid or missing token"

def test_upload_success(temp_storage):
    metadata = {
        "sys": 120,
        "dia": 80,
        "pul": 70,
        "timestamp": "2026-05-02T10:00:00+03:00",
        "device_model": "Test Device",
        "source": "manual",
        "corrected_by_user": False
    }
    
    files = {
        "file": ("test.jpg", b"fake-image-content", "image/jpeg"),
        "metadata": (None, json.dumps(metadata))
    }
    
    response = client.post(
        "/images/upload",
        headers={"Authorization": "Bearer test-token"},
        files=files
    )
    
    assert response.status_code == 201
    data = response.json()
    assert data["filename"] == "20260502_100000.jpg"
    assert data["folder"] == "2026-05"
    
    # Verify files exist
    assert (temp_storage / "2026-05" / "20260502_100000.jpg").exists()
    assert (temp_storage / "2026-05" / "20260502_100000.json").exists()

def test_upload_missing_metadata():
    files = {
        "file": ("test.jpg", b"content", "image/jpeg")
    }
    response = client.post(
        "/images/upload",
        headers={"Authorization": "Bearer test-token"},
        files=files
    )
    assert response.status_code == 422

def test_upload_invalid_metadata_range():
    metadata = {
        "sys": 999,  # Out of range
        "dia": 80,
        "pul": 70,
        "timestamp": "2026-05-02T10:00:00+03:00",
        "device_model": "Test",
        "source": "manual",
        "corrected_by_user": False
    }
    files = {
        "file": ("test.jpg", b"content", "image/jpeg"),
        "metadata": (None, json.dumps(metadata))
    }
    response = client.post(
        "/images/upload",
        headers={"Authorization": "Bearer test-token"},
        files=files
    )
    assert response.status_code == 422

def test_upload_unsupported_media_type():
    metadata = {
        "sys": 120,
        "dia": 80,
        "pul": 70,
        "timestamp": "2026-05-02T11:00:00+03:00",
        "device_model": "Test",
        "source": "manual",
        "corrected_by_user": False
    }
    files = {
        "file": ("test.txt", b"content", "text/plain"),
        "metadata": (None, json.dumps(metadata))
    }
    response = client.post(
        "/images/upload",
        headers={"Authorization": "Bearer test-token"},
        files=files
    )
    assert response.status_code == 415

def test_upload_collision(temp_storage):
    metadata = {
        "sys": 120,
        "dia": 80,
        "pul": 70,
        "timestamp": "2026-05-02T12:00:00+03:00",
        "device_model": "Test",
        "source": "manual",
        "corrected_by_user": False
    }
    files = {
        "file": ("test.jpg", b"content", "image/jpeg"),
        "metadata": (None, json.dumps(metadata))
    }
    
    # First upload
    response1 = client.post(
        "/images/upload",
        headers={"Authorization": "Bearer test-token"},
        files=files
    )
    assert response1.status_code == 201
    
    # Second upload same timestamp
    response2 = client.post(
        "/images/upload",
        headers={"Authorization": "Bearer test-token"},
        files=files
    )
    assert response2.status_code == 409
    assert response2.json()["detail"] == "photo for this timestamp already exists"

def test_upload_file_too_large():
    # Set limit to something very small for the test
    settings.max_file_size_mb = 0
    # 0 MB means max_file_size_bytes will be 0
    
    metadata = {
        "sys": 120,
        "dia": 80,
        "pul": 70,
        "timestamp": "2026-05-02T13:00:00+03:00",
        "device_model": "Test",
        "source": "manual",
        "corrected_by_user": False
    }
    files = {
        "file": ("large.jpg", b"x" * 100, "image/jpeg"),
        "metadata": (None, json.dumps(metadata))
    }
    
    response = client.post(
        "/images/upload",
        headers={"Authorization": "Bearer test-token"},
        files=files
    )
    assert response.status_code == 413
    assert "exceeds" in response.json()["detail"]
    
    # Reset for other tests if any (though this is the last one)
    settings.max_file_size_mb = 50
