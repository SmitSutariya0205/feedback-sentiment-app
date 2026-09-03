"""
config.py — Central configuration for the Feedback Sentiment API.

All tuneable values live here. Override via environment variables in production.
"""

import os

# ── Authentication ──────────────────────────────────────────────────────────────
# Single static Bearer token shared across the entire API.
# Override with the API_BEARER_TOKEN environment variable in production.
STATIC_BEARER_TOKEN: str = os.getenv("API_BEARER_TOKEN", "dev-secret-token")

# ── Database ────────────────────────────────────────────────────────────────────
DB_URL: str = os.getenv("DATABASE_URL", "sqlite:///./feedback.db")

# ── Logging ─────────────────────────────────────────────────────────────────────
LOG_LEVEL: str = os.getenv("LOG_LEVEL", "DEBUG")
LOG_FILE_PATH: str = os.getenv("LOG_FILE_PATH", "app.log")
LOG_MAX_BYTES: int = 5 * 1024 * 1024  # 5 MB per log file
LOG_BACKUP_COUNT: int = 3

# ── Metrics ─────────────────────────────────────────────────────────────────────
METRICS_CSV_PATH: str = os.getenv("METRICS_CSV_PATH", "metrics.csv")

# ── CORS Origins ─────────────────────────────────────────────────────────────────
# Whitelist of allowed client origins for CORS requests.
# Override in production via the ALLOWED_ORIGINS environment variable (comma-separated).
_DEFAULT_ORIGINS = (
    "https://orange-mud-08d0cc600.5.azurestaticapps.net,"
    "https://feedback-frontend-smit0205.azurestaticapps.net,"
    "http://localhost:5173,"
    "http://localhost:3000"
)
ALLOWED_ORIGINS: list[str] = [
    origin.strip()
    for origin in os.getenv("ALLOWED_ORIGINS", _DEFAULT_ORIGINS).split(",")
    if origin.strip()
]

# ── Public paths (exempt from Bearer token auth and middleware logging) ─────────
# Add any new unauthenticated routes here.
PUBLIC_PATHS: set[str] = {
    "/health",
    "/docs",
    "/openapi.json",
    "/redoc",
}

# ── Standard HTTP status messages (shared across handlers and routers) ──────────
STATUS_MESSAGES: dict[int, str] = {
    200: "Request processed successfully",
    201: "Feedback submitted and analyzed successfully",
    401: "Unauthorized",
    404: "Not Found",
    405: "Method Not Allowed",
    422: "Validation Error",
    500: "Internal Server Error",
}
