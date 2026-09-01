"""
context.py — Request-scoped context variables.

request_id_ctx carries the caller-supplied UUID for the lifetime of each request.
A custom logging.Filter (defined in main.py) reads this ContextVar and injects
the value into every LogRecord automatically, so no manual passing is needed.

For POST /feedback  → set inside the route handler after Pydantic parses the body.
For GET  /feedback  → set inside the route handler from the ?request_id= query param.

The middleware START log prints request_id=N/A for POST (body not yet parsed).
By the time the middleware END log runs, the ContextVar has been populated by
the route handler, so the END log shows the correct UUID.
"""

from contextvars import ContextVar

# Stores the string representation of the caller-supplied request UUID.
# Default "N/A" is used for log lines that fire before the route handler sets it
# (e.g. the middleware REQUEST START line for POST requests).
request_id_ctx: ContextVar[str] = ContextVar("request_id", default="N/A")
