"""
exceptions.py — Custom application exceptions and FastAPI exception handlers.

All handlers return the universal APIResponse envelope so that error responses
are structurally identical to success responses.

Error handling hierarchy (most → least specific):
    HTTPException           → custom_http_exception_handler    (401, 404, 500 raised in routers)
    RequestValidationError  → validation_exception_handler     (422 from Pydantic)
    SentimentAnalysisError  → app_exception_handler            (VADER runtime failure)
    Exception               → generic_exception_handler        (catch-all, 500)
"""

import logging

from fastapi import Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException

from config import STATUS_MESSAGES
from schemas import APIResponse

logger = logging.getLogger("feedback_api")


# ── Custom application exception ─────────────────────────────────────────────────

class SentimentAnalysisError(Exception):
    """
    Raised by sentiment.py when VADER's polarity_scores() fails at runtime.
    Carries a human-readable detail string that is safe to surface to the client.
    """

    def __init__(self, detail: str) -> None:
        self.detail = detail
        super().__init__(detail)


# ── Exception handlers ───────────────────────────────────────────────────────────

async def custom_http_exception_handler(
    request: Request, exc: HTTPException
) -> JSONResponse:
    """
    Handles all HTTPException instances (401, 404, explicit 500s, etc.).
    exc.detail is treated as the specific, client-facing error description.
    """
    message = STATUS_MESSAGES.get(exc.status_code, "Error")
    logger.warning(
        f"HTTP {exc.status_code} on {request.method} {request.url.path} — {exc.detail}"
    )
    body = APIResponse(
        success=False,
        status_code=exc.status_code,
        message=message,
        error_message=str(exc.detail),
        data=None,
    )
    return JSONResponse(
        status_code=exc.status_code,
        content=body.model_dump(mode="json"),
    )


async def validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    """
    Handles Pydantic RequestValidationError (FastAPI raises 422).
    Collects all field-level errors and joins them into a single readable string
    so the client sees all problems in one response.
    """
    error_parts: list[str] = []
    for error in exc.errors():
        # Strip leading "body" from location path for cleaner messages
        loc_parts = [str(p) for p in error["loc"] if p != "body"]
        loc = " -> ".join(loc_parts) if loc_parts else "request"
        error_parts.append(f"{loc}: {error['msg']}")

    error_message = "; ".join(error_parts)
    logger.warning(
        f"Validation error on {request.method} {request.url.path} — {error_message}"
    )
    body = APIResponse(
        success=False,
        status_code=422,
        message=STATUS_MESSAGES[422],
        error_message=error_message,
        data=None,
    )
    return JSONResponse(
        status_code=422,
        content=body.model_dump(mode="json"),
    )


async def app_exception_handler(
    request: Request, exc: SentimentAnalysisError
) -> JSONResponse:
    """
    Handles SentimentAnalysisError — VADER runtime failure.
    The detail is safe to surface; the full traceback is logged server-side.
    """
    error_message = f"Sentiment analysis failed: {exc.detail}"
    logger.error(
        f"SentimentAnalysisError on {request.method} {request.url.path} — {exc.detail}",
        exc_info=True,
    )
    body = APIResponse(
        success=False,
        status_code=500,
        message=STATUS_MESSAGES[500],
        error_message=error_message,
        data=None,
    )
    return JSONResponse(
        status_code=500,
        content=body.model_dump(mode="json"),
    )


async def generic_exception_handler(
    request: Request, exc: Exception
) -> JSONResponse:
    """
    Catch-all for any unhandled exception.
    Returns a deliberately vague error message to avoid leaking implementation
    details. Full traceback is logged at ERROR level.
    """
    logger.error(
        f"Unhandled exception on {request.method} {request.url.path} — {exc!r}",
        exc_info=True,
    )
    body = APIResponse(
        success=False,
        status_code=500,
        message=STATUS_MESSAGES[500],
        error_message="An unexpected error occurred. Please try again later.",
        data=None,
    )
    return JSONResponse(
        status_code=500,
        content=body.model_dump(mode="json"),
    )
