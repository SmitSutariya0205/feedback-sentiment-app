# Product Feedback Sentiment API

A FastAPI backend that accepts product feedback text, analyses sentiment using **VADER** (CPU-friendly, no GPU required), stores results in SQLite, and exposes authenticated REST endpoints.

---

## Features

- **VADER sentiment analysis** — positive / negative / neutral with a confidence score
- **Single static Bearer token** — shared API key, no user registration
- **Request tracing** — caller-supplied UUID (`request_id`) flows through every log line
- **Unified response envelope** — `APIResponse[T]` for all success and error responses
- **Persistent metrics** — `metrics.csv` appended after every authenticated request
- **Rotating log file** — `app.log` (5 MB × 3 backups)
- **Fail-fast startup** — VADER init failure prevents the server from accepting requests

---

## Setup

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

### 2. Environment variables (optional — defaults shown)

| Variable | Default | Description |
|---|---|---|
| `API_BEARER_TOKEN` | `dev-secret-token` | Static Bearer token for the entire API |
| `DATABASE_URL` | `sqlite:///./feedback.db` | SQLAlchemy DB connection string |
| `LOG_LEVEL` | `DEBUG` | Logging level (`DEBUG`, `INFO`, `WARNING`, `ERROR`) |
| `LOG_FILE_PATH` | `app.log` | Path for the rotating log file |
| `METRICS_CSV_PATH` | `metrics.csv` | Path for the metrics CSV |

### 3. Run the server

```bash
uvicorn main:app --reload
```

Server starts at **http://localhost:8000**

---

## API Reference

### Authentication

All endpoints except `/health`, `/docs`, `/openapi.json`, and `/redoc` require:

```
Authorization: Bearer <token>
```

### Endpoints

#### `POST /feedback` — Submit feedback

**Request body:**
```json
{
  "request_id": "550e8400-e29b-41d4-a716-446655440000",
  "user_id": "alice",
  "product_name": "Widget Pro",
  "feedback_text": "This product is absolutely fantastic! I love it."
}
```

**Success response (`201`):**
```json
{
  "success": true,
  "status_code": 201,
  "message": "Feedback submitted and analyzed successfully",
  "error_message": null,
  "data": {
    "id": 1,
    "request_id": "550e8400-e29b-41d4-a716-446655440000",
    "user_id": "alice",
    "product_name": "Widget Pro",
    "feedback_text": "This product is absolutely fantastic! I love it.",
    "sentiment_label": "positive",
    "confidence_score": 0.9382,
    "created_at": "2026-08-14T05:40:01.123456+00:00"
  }
}
```

---

#### `GET /feedback/{user_id}?request_id=<uuid>` — Get user feedback

Returns all feedback records for a user (newest first).
Returns `200` with an empty list if the user has no records.

**Success response (`200`):**
```json
{
  "success": true,
  "status_code": 200,
  "message": "Request processed successfully",
  "error_message": null,
  "data": {
    "user_id": "alice",
    "total": 1,
    "feedbacks": [...]
  }
}
```

---

#### `GET /health` — Liveness probe (no auth required)

```json
{
  "success": true,
  "status_code": 200,
  "message": "Service is healthy",
  "error_message": null,
  "data": null
}
```

---

### Error response format (all errors)

```json
{
  "success": false,
  "status_code": 422,
  "message": "Validation Error",
  "error_message": "request_id: Value is not a valid UUID; feedback_text: String should have at least 5 characters",
  "data": null
}
```

---

## Output Files

| File | Description |
|---|---|
| `feedback.db` | SQLite database — auto-created on first run |
| `app.log` | Structured request logs with `request_id` tracing |
| `metrics.csv` | Per-request metrics, one row appended per authenticated request |

---

## Interactive Docs

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
