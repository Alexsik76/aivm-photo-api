# aivm-photo-api

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

**Request:** `multipart/form-data`
- `file`: Image bytes (JPG, PNG, etc.)
- `metadata`: JSON string matching the `PhotoMetadata` schema.

**Metadata Example (Uncorrected):**
```json
{
  "sys": 120,
  "dia": 80,
  "pul": 70,
  "timestamp": "2026-05-02T10:00:00+03:00",
  "device_model": "Paramed Expert-X",
  "source": "user_confirmed",
  "corrected_by_user": false
}
```

**Metadata Example (Corrected by user):**
```json
{
  "sys": 125,
  "dia": 82,
  "pul": 70,
  "timestamp": "2026-05-02T10:05:00+03:00",
  "device_model": "Paramed Expert-X",
  "source": "user_confirmed",
  "corrected_by_user": true,
  "gemini_suggested": {
    "sys": 120,
    "dia": 80,
    "pul": 70
  }
}
```

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
- **Metadata:** Verify `corrected_by_user` and `gemini_suggested` fields accurately reflect user interaction in BP Tracker.
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
