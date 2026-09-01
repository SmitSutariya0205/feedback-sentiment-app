"""
fields.py — Reusable Annotated Pydantic field type aliases.

Each alias is the single source of truth for its validation rules.
Request and response schemas in schemas.py compose these types — no inline
Field(...) calls appear in the schema definitions themselves.
"""

from typing import Annotated
from uuid import UUID

from pydantic import Field

# ── Identity / tracing ──────────────────────────────────────────────────────────

RequestId = Annotated[
    UUID,
    Field(description="Unique request UUID provided by the caller for end-to-end tracing"),
]

UserId = Annotated[
    int,
    Field(
        ge=1,
        description="Numeric identifier of the user submitting feedback",
    ),
]

# ── Product ─────────────────────────────────────────────────────────────────────

ProductName = Annotated[
    str,
    Field(
        min_length=1,
        max_length=200,
        description="Name of the product being reviewed",
    ),
]

# ── Feedback content ─────────────────────────────────────────────────────────────

FeedbackText = Annotated[
    str,
    Field(
        min_length=5,
        max_length=2000,
        description="Raw product feedback text provided by the user",
    ),
]

# ── Sentiment ────────────────────────────────────────────────────────────────────

SentimentLabel = Annotated[
    str,
    Field(
        pattern="^(positive|negative|neutral)$",
        description="Sentiment classification: positive, negative, or neutral",
    ),
]

ConfidenceScore = Annotated[
    float,
    Field(
        ge=0.0,
        le=1.0,
        description="Confidence score in [0.0, 1.0] derived from the VADER compound score",
    ),
]
