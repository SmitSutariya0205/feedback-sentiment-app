"""
auth.py — Bearer token authentication dependency.

A single static token (STATIC_BEARER_TOKEN from config.py) protects all
non-public endpoints. The token is validated using secrets.compare_digest
to prevent timing-based side-channel attacks.

This dependency is declared on route handlers primarily for OpenAPI / Swagger UI
visibility (the padlock icon). The actual first-pass auth check is done in
CombinedMiddleware before the route handler runs.
"""

import logging
import secrets

from fastapi import HTTPException, Security
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from typing import Optional

from config import STATIC_BEARER_TOKEN

logger = logging.getLogger("feedback_api")

_bearer_scheme = HTTPBearer(
    scheme_name="BearerToken",
    description="Static API Bearer token. Include as: Authorization: Bearer <token>",
    auto_error=False,  # Return None instead of raising 403 when header is absent;
                       # our verify_token raises 401 instead for consistency.
)


def verify_token(
    credentials: Optional[HTTPAuthorizationCredentials] = Security(_bearer_scheme),
) -> None:
    """
    FastAPI Security dependency.

    Validates the Bearer token against STATIC_BEARER_TOKEN.
    Raises 401 if the header is absent or the token is invalid.
    Returns None on success (no user context needed).

    This is the route-level guardrail that also powers the Swagger UI padlock.
    The middleware performs the same check earlier in the request lifecycle.
    """
    if credentials is None or not secrets.compare_digest(
        credentials.credentials, STATIC_BEARER_TOKEN
    ):
        logger.warning("Route-level auth: invalid or missing Bearer token rejected")
        raise HTTPException(status_code=401, detail="Invalid or missing Bearer token")
