"""
schemas.py — Pydantic request / response schemas.

All schemas compose reusable field types from fields.py.
The universal APIResponse[T] envelope wraps every endpoint response —
both successes and errors — to provide a consistent client contract.
"""

from __future__ import annotations

from datetime import datetime
from typing import Generic, Optional, TypeVar

from pydantic import BaseModel, ConfigDict

from fields import (
    ConfidenceScore,
    FeedbackText,
    ProductName,
    RequestId,
    SentimentLabel,
    UserId,
)

T = TypeVar("T")


# ── Universal response envelope ─────────────────────────────────────────────────

class APIResponse(BaseModel, Generic[T]):
    """
    Uniform envelope returned by every endpoint.

    Successful responses:
        success=True, error_message=None, data=<payload>

    Error responses:
        success=False, data=None, error_message=<specific detail>
    """

    success: bool
    status_code: int
    message: str
    error_message: Optional[str] = None
    data: Optional[T] = None


# ── Request schemas ──────────────────────────────────────────────────────────────

class FeedbackRequest(BaseModel):
    """Body accepted by POST /feedback."""

    request_id: RequestId
    user_id: UserId
    product_name: ProductName
    feedback_text: FeedbackText


# ── Response data schemas ────────────────────────────────────────────────────────

class FeedbackResponse(BaseModel):
    """Single analysed feedback record returned inside APIResponse.data."""

    id: int
    request_id: RequestId
    user_id: UserId
    product_name: ProductName
    feedback_text: FeedbackText
    sentiment_label: SentimentLabel
    confidence_score: ConfidenceScore
    created_at: datetime

    # Allow construction directly from SQLAlchemy ORM objects.
    model_config = ConfigDict(from_attributes=True)


class FeedbackListResponse(BaseModel):
    """Paginated list of feedback records for a user, returned inside APIResponse.data."""

    user_id: UserId
    total: int
    feedbacks: list[FeedbackResponse]
