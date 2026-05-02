# aivm-photo-api

REST API for receiving and storing photos of blood-pressure-monitor screens with metadata for machine learning. 
For more context, see [plan_blood_pressure_ml.md](docs/plan_blood_pressure_ml.md).

## API Contract

### `POST /images/upload`

Upload an image with metadata. Requires Bearer token authentication.

**Authentication:** `Authorization: Bearer <API_TOKEN>`

**Request:** `multipart/form-data`
- `file`: Image bytes (JPG, PNG, etc.)
- `metadata`: JSON string matching the `PhotoMetadata` schema.

**Metadata Example:**
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
- `401`: Unauthorized (missing or invalid token)
- `409`: Conflict (photo for this timestamp already exists)
- `413`: File size too large
- `415`: Unsupported image format
- `422`: Validation error (invalid metadata)

### `GET /health`

Liveness check. Returns `{"status": "ok"}`.

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

The service is containerised and deployed via Docker Compose. The Compose stack mounts the TrueNAS SMB share directly via a named volume; the host requires no fstab entry. NAS credentials are provided via `.env` (`NAS_USER`, `NAS_PASSWORD`).

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
