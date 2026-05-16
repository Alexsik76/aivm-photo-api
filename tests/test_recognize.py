import os
import pytest
from fastapi.testclient import TestClient
from unittest.mock import MagicMock, patch
import numpy as np

# Mock environment variables before importing app
os.environ["API_TOKEN"] = "test-token"
os.environ["STORAGE_PATH"] = "/tmp/test-photos"

# We mock load_models entirely to avoid YOLO class instantiation
with patch("app.ml.models.load_models") as mock_load:
    mock_load.return_value = (MagicMock(), MagicMock())
    from app.main import app

@pytest.fixture
def mock_models_state():
    # Setup mock return values for models already in app.state
    mock_display = MagicMock()
    mock_digits = MagicMock()
    
    app.state.display_model = mock_display
    app.state.digit_model = mock_digits
    yield mock_display, mock_digits

def test_recognize_no_auth():
    client = TestClient(app)
    response = client.post("/images/recognize")
    assert response.status_code == 401

def test_recognize_success(mock_models_state):
    mock_display, mock_digits = mock_models_state
    
    # Mock display model result
    mock_box = MagicMock()
    mock_box.xyxy = [MagicMock()]
    mock_box.xyxy[0].cpu().numpy.return_value = np.array([10, 10, 100, 100])
    mock_box.conf.cpu().numpy.return_value = np.array([0.9])
    
    mock_boxes_display = MagicMock()
    mock_boxes_display.__len__.return_value = 1
    mock_boxes_display.__getitem__.return_value = mock_box
    mock_boxes_display.conf.cpu().numpy.return_value = np.array([0.9])
    
    mock_display_result = MagicMock()
    mock_display_result.boxes = mock_boxes_display
    mock_display.return_value = [mock_display_result]
    
    # Mock digit model results
    mock_boxes_digits = MagicMock()
    mock_boxes_digits.__len__.return_value = 6
    mock_boxes_digits.xyxy.cpu().numpy.return_value = np.array([
        [10, 20, 30, 40], [40, 20, 60, 40],
        [10, 220, 30, 240], [40, 220, 60, 240],
        [10, 420, 30, 440], [40, 420, 60, 440]
    ])
    mock_boxes_digits.conf.cpu().numpy.return_value = np.array([0.9]*6)
    mock_boxes_digits.cls.cpu().numpy.return_value = np.array([1, 2, 7, 5, 8, 0])
    
    mock_digit_result = MagicMock()
    mock_digit_result.boxes = mock_boxes_digits
    mock_digits.return_value = [mock_digit_result]
    
    client = TestClient(app)
    import cv2
    _, img_encoded = cv2.imencode(".jpg", np.zeros((100, 100, 3), dtype=np.uint8))
    img_bytes = img_encoded.tobytes()
    
    response = client.post(
        "/images/recognize",
        headers={"Authorization": "Bearer test-token"},
        files={"file": ("test.jpg", img_bytes, "image/jpeg")}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["sys"] == 12
    assert data["dia"] == 75
    assert data["pul"] == 80
