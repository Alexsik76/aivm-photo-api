# aivm-photo-api

REST API for receiving and storing images submitted by AI agents.

## Requirements

- Python 3.9+
- pip

## Installation

```bash
pip install -r requirements.txt
```

## Configuration

All settings are controlled via environment variables. Defaults are shown below.

| Variable           | Default         | Description                        |
|--------------------|-----------------|------------------------------------|
| `STORAGE_PATH`     | `/mnt/dataset`  | Directory where images are saved   |
| `MAX_FILE_SIZE_MB` | `50`            | Maximum allowed upload size in MB  |

**Accepted content types:** `image/jpeg`, `image/png`, `image/gif`, `image/webp`, `image/bmp`, `image/tiff`

## Running

```bash
uvicorn main:app --host 0.0.0.0 --port 8000
```

For development with auto-reload:

```bash
uvicorn main:app --reload
```

Interactive API docs are available at `http://localhost:8000/docs`.

## API

### `GET /health`

Liveness check.

**Response `200`**
```json
{ "status": "ok" }
```

---

### `POST /images/upload`

Upload a single image. The request must use `multipart/form-data`.

| Field  | Type   | Required | Description     |
|--------|--------|----------|-----------------|
| `file` | binary | yes      | Image to upload |

**Response `201`**
```json
{
  "filename": "a3f1c8e2...d4.jpg",
  "size_bytes": 204800,
  "content_type": "image/jpeg"
}
```

**Error responses**

| Status | Cause                                    |
|--------|------------------------------------------|
| `413`  | File exceeds `MAX_FILE_SIZE_MB`          |
| `415`  | Content type not in the accepted list    |

### `POST /webhook`

GitHub webhook endpoint for automatic deployment. Triggers code update (`git pull`), dependency installation, and service restart via a background task.

| Query Parameter | Type   | Required | Description                     |
|-----------------|--------|----------|---------------------------------|
| `token`         | string | yes      | Secret token for authentication |

**Response `200`**
```json
{ "status": "Update triggered" }

**Error responses**

| Status | Cause                                    |
|--------|------------------------------------------|
| `403`  | Invalid or missing authentication token  |


## Project structure

```
aivm-photo-api/
├── main.py          # FastAPI app and endpoint definitions
├── storage.py       # FileValidator and FileStorage classes
├── config.py        # Settings resolved from environment variables
└── requirements.txt
```

## Architecture notes

- **`FileValidator`** and **`FileStorage`** are deliberately separate classes (SRP). Validation never touches disk; storage never validates.
- Saved filenames are UUID-based and the extension is derived from the validated `Content-Type`, not the original filename, to prevent path traversal.
- The storage directory is created automatically on startup if it does not exist.
