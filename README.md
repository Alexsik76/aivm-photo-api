# aivm-photo-api

FastAPI service for storing blood pressure monitor photos and recognizing digits using ML.

## Features

- **Store photos**: Saves photos and metadata to an SMB-mounted NAS share.
- **ML Recognition**: Recognizes SYS, DIA, and PUL values from photos using YOLOv8 models.
- **Local Processing**: Recognition happens entirely on CPU in ~50ms.

## API Endpoints

### 1. Recognition
`POST /images/recognize`

Recognizes blood pressure values from an uploaded image.

**Request:**
- `file`: image bytes (multipart/form-data)

**Response (200 OK):**
```json
{
  "sys": 125,
  "dia": 74,
  "pul": 73,
  "confidence": 0.87,
  "elapsed_ms": 52
}
```

### 2. Upload
`POST /images/upload`

Stores the photo and metadata to disk.

**Request:** `multipart/form-data` — flat form fields (see full API Contract section below).

### 3. Health
`GET /health` -> `{"status": "ok"}`

## Installation & Deployment

### Manual Model Setup
Before building the container, you must manually copy the trained YOLOv8 models from the `bp-ocr-cnn` project:
1. `bp-ocr-cnn/runs/detect/display_detector_v1/weights/best.pt` -> `models/display.pt`
2. `bp-ocr-cnn/runs/detect/digit_detector_latest/weights/best.pt` -> `models/digits.pt`

### Docker Compose
```bash
docker-compose up -d --build
```

## Project Structure
The project is organized as a package in the `app/` directory:
- `app/main.py`: Entry point, lifespan, and route registration.
- `app/ml/`: ML pipeline, postprocessing, and model loading.
- `app/routes/`: API route handlers.
- `app/storage.py`: File storage and validation logic.
- `models/`: YOLO model files.

REST API for receiving and storing photos of blood-pressure-monitor screens with metadata for machine learning. 
For more context, see [plan_blood_pressure_ml.md](docs/plan_blood_pressure_ml.md).

## Who calls this service

The only client today is **[bptracker-backend](../bptracker-backend/README.md)** (`PhotoApiService` class).

- **Flow:** When a user saves a measurement that originated from a photo, the backend saves the record to its DB and then asynchronously forwards the photo + metadata to this service.
- **Reliability:** The call is "fire-and-forget" from the backend's perspective. It does not retry on failure; photos lost during an outage are not recovered.
- **Authentication:** Requires a static Bearer token (`PHOTO_API_TOKEN` in both repos).

## API Contract

### `POST /images/upload`

Upload an image with metadata. Requires Bearer token authentication.

**Authentication:** `Authorization: Bearer <API_TOKEN>`

**Request:** `multipart/form-data` — all fields are individual form params.

| Field | Type | Required | Notes |
|---|---|---|---|
| `file` | image bytes | Yes | JPG, PNG, etc. |
| `sys` | int | Yes | 50–300 |
| `dia` | int | Yes | 30–200 |
| `pul` | int | Yes | 30–250 |
| `timestamp` | datetime (ISO 8601 with TZ) | Yes | e.g. `2026-05-02T10:00:00+03:00` |
| `source` | enum | Yes | `local_ocr`, `gemini`, `gemini_auto`, `manual`, `user_confirmed` |
| `corrected_by_user` | bool | Yes | `true` / `false` |
| `device_model` | string | No | defaults to `"unknown"` |
| `ai_suggested_sys` | int | No | 50–300 |
| `ai_suggested_dia` | int | No | 30–200 |
| `ai_suggested_pul` | int | No | 30–250 |
| `notes` | string | No | |
| `ocr_meta` | JSON string | No | `OcrMeta` schema (see below) |

**`ocr_meta` JSON schema:**
```json
{
  "engine": "local",
  "model_version": "int8_v1",
  "inference_ms": { "display": 120, "digits": 95, "postprocess": 5 },
  "confidence": { "min": 0.71, "mean": 0.84 },
  "fallback_reason": null,
  "user_agent": "Mozilla/5.0 ...",
  "hw_concurrency": 8
}
```

The OpenAPI spec is generated via `python export_openapi.py` and committed as `openapi.json`. Frontend TypeScript types are generated from it via `npm run generate:types` in `bptracker-frontend`.

**Success Response (201):**
```json
{
  "filename": "20260502_100000.jpg",
  "folder": "2026-05",
  "size_bytes": 234567
}
```

**Status Codes:**
- `201`: Success
- `401`: Unauthorized
- `409`: Conflict (already exists)
- `413`: File size too large
- `415`: Unsupported image format
- `422`: Validation error

### `GET /health`

Liveness check. Returns `{"status": "ok"}`.

## Verifying integration

- **Storage:** Check `<STORAGE_PATH>/YYYY-MM/` for incoming files. Each upload creates a `.jpg` and a `.json` sidecar.
- **Metadata:** Verify `corrected_by_user` and `ai_suggested` fields accurately reflect user interaction in BP Tracker.
- **Logs:** View container logs for errors: `docker logs aivm-photo-api`.

## Local Development

1. Create a virtual environment:
   ```bash
   python -m venv .venv
   .\.venv\Scripts\activate  # Windows
   source .venv/bin/activate # Linux/macOS
   ```
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Set environment variables (or create `.env`):
   ```
   API_TOKEN=your-secret-token
   STORAGE_PATH=./data/photos
   ```
4. Run locally:
   ```bash
   uvicorn main:app --reload
   ```

## Running Tests

```bash
$env:PYTHONPATH="."; .\.venv\Scripts\pytest -v
```

## Deployment

The service is containerised and deployed via Docker Compose. The Compose stack mounts the TrueNAS SMB share directly via a named volume. NAS credentials are provided via `.env` (`NAS_USER`, `NAS_PASSWORD`).

To deploy:
```bash
docker-compose up -d --build
```

## Storage Layout

Files are stored on the SMB share in the following structure:
```
/data/photos/
  2026-04/
    20260417_093532.jpg
    20260417_093532.json
  2026-05/
    ...
```

## Environment Variables

| Variable           | Required | Default        | Description                          |
|--------------------|----------|----------------|--------------------------------------|
| `API_TOKEN`        | Yes      | -              | Bearer token for authentication      |
| `STORAGE_PATH`     | No       | `/data/photos` | Path to store images and metadata    |
| `MAX_FILE_SIZE_MB` | No       | `50`           | Maximum allowed upload size in MB    |
| `NAS_USER`         | Yes      | -              | Username for NAS SMB share           |
| `NAS_PASSWORD`     | Yes      | -              | Password for NAS SMB share           |
