"""
middleware.py — CombinedMiddleware: auth + logging + metrics in one pass.

Request lifecycle for every NON-public path:
    0.  Path in PUBLIC_PATHS?  → short-circuit, no auth/log/metrics.
    1.  Validate Bearer token  → return 401 APIResponse immediately if invalid.
    2.  Log REQUEST START      → request_id=N/A for POST (body not yet read).
    3.  Start perf timer.
    4.  Route handler runs     → sets request.state.request_id (and optionally
                                  request.state.sentiment_label / confidence_score).
    5.  Stop timer.
    6.  Log REQUEST END        → request_id now available via request.state.
    7.  Update MetricsStore + append CSV row.
    8.  Return response.

Why request.state instead of a pure ContextVar for cross-middleware communication:
    BaseHTTPMiddleware uses Starlette's streaming adapter for call_next, which
    means the route handler may execute in a context where ContextVar mutations
    do not reliably propagate back to the middleware coroutine. request.state is
    attached to the Request object itself and is always accessible from both sides.
    The ContextVar is still set in the route handler for log lines emitted *within*
    the handler (where the ContextVar is live).
"""

import logging
import secrets
import time

try:
    from opentelemetry import trace as otel_trace
    _HAS_OTEL = True
except ImportError:
    _HAS_OTEL = False

from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from config import PUBLIC_PATHS, STATIC_BEARER_TOKEN, STATUS_MESSAGES
from context import request_id_ctx
from metrics import metrics_store
from schemas import APIResponse

logger = logging.getLogger("feedback_api")


class CombinedMiddleware(BaseHTTPMiddleware):
    """Single middleware handling auth, structured logging, and metrics."""

    async def dispatch(self, request: Request, call_next) -> Response:
        path = request.url.path

        # ── Step 0: Public path bypass ──────────────────────────────────────────
        if path in PUBLIC_PATHS:
            return await call_next(request)

        method = request.method
        client_ip = request.client.host if request.client else "unknown"

        # ── Step 1: Bearer token validation ─────────────────────────────────────
        auth_header = request.headers.get("Authorization", "")
        if not auth_header.startswith("Bearer "):
            logger.warning(
                f"Auth failure: missing Bearer token | {method} {path} | ip={client_ip}"
            )
            return self._unauthorized_response("Invalid or missing Bearer token")

        token = auth_header[len("Bearer "):]
        if not secrets.compare_digest(token, STATIC_BEARER_TOKEN):
            logger.warning(
                f"Auth failure: invalid Bearer token | {method} {path} | ip={client_ip}"
            )
            return self._unauthorized_response("Invalid or missing Bearer token")

        # ── Step 2: Log request start ────────────────────────────────────────────
        # Extract request_id from query params for GET requests.
        # For POST requests, it remains N/A here (body not yet parsed).
        initial_request_id = request.query_params.get("request_id", "N/A")
        request.state.request_id = initial_request_id
        request_id_ctx.set(initial_request_id)

        # ── Attach request_id to the active OpenTelemetry span ────────────────
        if _HAS_OTEL:
            span = otel_trace.get_current_span()
            if span and span.is_recording():
                span.set_attribute("request_id", initial_request_id)
                span.set_attribute("http.client_ip", client_ip)

        logger.info(f"Request started | method={method} path={path} ip={client_ip}")

        # ── Step 3: Start timer ──────────────────────────────────────────────────
        t_start = time.perf_counter()
        response = None

        # ── Step 4: Run route handler (+ exception handlers) ────────────────────
        try:
            response = await call_next(request)
        except Exception as exc:
            # This path is very rare — Starlette's own ExceptionMiddleware should
            # catch everything first. Log it and re-raise so uvicorn handles it.
            execution_time_ms = (time.perf_counter() - t_start) * 1000
            request_id = getattr(request.state, "request_id", "N/A")
            request_id_ctx.set(request_id)
            logger.error(
                f"Unhandled exception escaped route handler | "
                f"method={method} path={path} time={execution_time_ms:.2f}ms | {exc!r}",
                exc_info=True,
            )
            raise
        finally:
            # ── Steps 5-7 always run, even on exception ──────────────────────────
            if response is not None:
                execution_time_ms = (time.perf_counter() - t_start) * 1000
                request_id = getattr(request.state, "request_id", "N/A")
                request_id_ctx.set(request_id)

                # ── Update span with final request_id (POST sets it in handler) ───
                if _HAS_OTEL:
                    span = otel_trace.get_current_span()
                    if span and span.is_recording():
                        span.set_attribute("request_id", request_id)
                        sentiment = getattr(request.state, "sentiment_label", None)
                        confidence = getattr(request.state, "confidence_score", None)
                        if sentiment:
                            span.set_attribute("sentiment_label", sentiment)
                        if confidence is not None:
                            span.set_attribute("confidence_score", confidence)

                # ── Step 6: Log request end ──────────────────────────────────────
                logger.info(
                    f"Request completed | method={method} path={path} "
                    f"status={response.status_code} time={execution_time_ms:.2f}ms"
                )

                # ── Step 7: Update metrics ───────────────────────────────────────
                sentiment_label = getattr(request.state, "sentiment_label", None)
                confidence_score = getattr(request.state, "confidence_score", None)

                metrics_store.record_request(
                    request_id=request_id,
                    method=method,
                    path=path,
                    status_code=response.status_code,
                    execution_time_ms=execution_time_ms,
                    sentiment_label=sentiment_label,
                    confidence_score=confidence_score,
                )

        return response

    @staticmethod
    def _unauthorized_response(detail: str) -> JSONResponse:
        """Build a 401 APIResponse envelope without going through a route handler."""
        body = APIResponse(
            success=False,
            status_code=401,
            message=STATUS_MESSAGES[401],
            error_message=detail,
            data=None,
        )
        return JSONResponse(
            status_code=401,
            content=body.model_dump(mode="json"),
        )
