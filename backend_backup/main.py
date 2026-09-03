"""
main.py — FastAPI application entry point.

Responsibilities:
    1. Configure structured logging (StreamHandler + RotatingFileHandler).
       A custom logging.Filter injects request_id from the ContextVar into
       every LogRecord so every log line carries the tracing UUID automatically.
    2. Define the lifespan context manager:
         - Startup: initialise VADER, create DB tables. Fail fast if VADER fails.
         - Shutdown: clean log message.
    3. Create and configure the FastAPI app:
         - Attach CombinedMiddleware (auth + logging + metrics).
         - Register all exception handlers.
         - Include routers.
         - Expose /health as a public, unauthenticated endpoint.
"""

import logging
import logging.handlers
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

from config import ALLOWED_ORIGINS, LOG_BACKUP_COUNT, LOG_FILE_PATH, LOG_LEVEL, LOG_MAX_BYTES
from context import request_id_ctx
from database import Base, engine
from exceptions import (
    SentimentAnalysisError,
    app_exception_handler,
    custom_http_exception_handler,
    generic_exception_handler,
    validation_exception_handler,
)
from middleware import CombinedMiddleware
from routers import feedback
from schemas import APIResponse


# ── Logging setup ────────────────────────────────────────────────────────────────
class _RequestIdFilter(logging.Filter):
    """
    Injects the current request_id from the ContextVar into every LogRecord.
    Attached to all handlers of the 'feedback_api' logger so the request_id
    appears in every log line without any manual passing.
    """

    def filter(self, record: logging.LogRecord) -> bool:
        record.request_id = request_id_ctx.get()  # type: ignore[attr-defined]
        return True


def _setup_logging() -> logging.Logger:
    formatter = logging.Formatter(
        fmt=(
            "%(asctime)s | %(levelname)-8s | "
            "[request_id=%(request_id)s] | %(message)s"
        ),
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    request_id_filter = _RequestIdFilter()

    # Create logger first so we can add handlers to it safely
    logger = logging.getLogger("feedback_api")
    logger.setLevel(getattr(logging, LOG_LEVEL.upper(), logging.DEBUG))
    logger.propagate = False  # Prevent double-logging via root logger

    # Console handler
    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)
    stream_handler.addFilter(request_id_filter)
    logger.addHandler(stream_handler)

    # Rotating file handler (5 MB per file, 3 backups)
    try:
        file_handler = logging.handlers.RotatingFileHandler(
            LOG_FILE_PATH,
            maxBytes=LOG_MAX_BYTES,
            backupCount=LOG_BACKUP_COUNT,
            encoding="utf-8",
        )
        file_handler.setFormatter(formatter)
        file_handler.addFilter(request_id_filter)
        logger.addHandler(file_handler)
    except (OSError, PermissionError) as exc:
        # Fall back to console-only logging — never crash the app over a log file
        stream_handler.stream.write(
            f"WARNING: Could not open log file '{LOG_FILE_PATH}': {exc}. "
            "Logging to console only.\n"
        )

    return logger


# Initialise logging at import time so the lifespan can use the logger.
_logger = _setup_logging()


# ── Lifespan ─────────────────────────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application startup / shutdown lifecycle.

    Startup:
        1. Create all SQLAlchemy DB tables (no-op if already present).
        2. Initialise VADER SentimentIntensityAnalyzer and store in app.state.vader.
           If initialisation fails, RuntimeError is raised → uvicorn exits →
           no requests are ever accepted.

    Shutdown:
        Log a clean shutdown message.
    """
    # ── Startup ────────────────────────────────────────────────────────────────
    _logger.info("=== Application starting up ===")

    _logger.info("Creating database tables (if not exist)...")
    try:
        Base.metadata.create_all(bind=engine)
        _logger.info("Database tables ready.")
    except Exception as exc:
        _logger.critical(
            f"Database table creation FAILED: {exc}. "
            "Application cannot start without a working database."
        )
        raise RuntimeError("Database initialisation failed") from exc

    _logger.info("Initialising VADER SentimentIntensityAnalyzer...")
    try:
        app.state.vader = SentimentIntensityAnalyzer()
        _logger.info("VADER initialised successfully — ready to serve requests.")
    except Exception as exc:
        _logger.critical(
            f"VADER initialisation FAILED: {exc}. "
            "Application cannot start without the sentiment model."
        )
        raise RuntimeError("Sentiment model failed to initialise") from exc

    yield  # ← Application is live and serving requests here

    # ── Shutdown ───────────────────────────────────────────────────────────────
    _logger.info("=== Application shutting down ===")


# ── FastAPI application ───────────────────────────────────────────────────────────

app = FastAPI(
    title="Product Feedback Sentiment API",
    description=(
        "Submit product feedback text and receive VADER-based sentiment analysis. "
        "All endpoints require a static Bearer token. "
        "Every request is traced end-to-end via a caller-supplied request_id (UUID)."
    ),
    version="1.0.0",
    lifespan=lifespan,
)

# ── Middleware (registered in reverse application order) ──────────────────────────
# CombinedMiddleware (auth, logging, metrics)
app.add_middleware(CombinedMiddleware)

# CORSMiddleware registered after CombinedMiddleware so CORSMiddleware is outer
# and can handle preflight OPTIONS requests before auth checks
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)


# ── Security Headers Middleware ──────────────────────────────────────────────────
@app.middleware("http")
async def add_security_headers(request, call_next):
    """Inject standard OWASP security headers into all responses."""
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    return response

# ── Exception handlers ────────────────────────────────────────────────────────────
# Registration order: least-specific first so more-specific handlers take priority.
app.add_exception_handler(Exception, generic_exception_handler)
app.add_exception_handler(SentimentAnalysisError, app_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(HTTPException, custom_http_exception_handler)

# ── Routers ───────────────────────────────────────────────────────────────────────
app.include_router(feedback.router)


# ── Public endpoints ──────────────────────────────────────────────────────────────

@app.get(
    "/health",
    tags=["Health"],
    summary="Liveness probe — no authentication required",
    response_model=APIResponse[None],
)
def health_check() -> APIResponse[None]:
    """Returns 200 when the service is up. No Bearer token required."""
    return APIResponse(
        success=True,
        status_code=200,
        message="Service is healthy",
    )
