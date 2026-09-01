"""
models.py — SQLAlchemy ORM models.

FeedbackRecord is the only table. It stores the submitted feedback,
the resolved sentiment label, and the derived confidence score.
Raw VADER sub-scores (pos, neg, neu, compound) are intentionally NOT stored
— only the final confidence_score is persisted.
"""

from datetime import datetime, timezone

from sqlalchemy import DateTime, Float, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from database import Base


class FeedbackRecord(Base):
    """Persisted record of a single feedback submission and its sentiment analysis."""

    __tablename__ = "feedback_records"

    id: Mapped[int] = mapped_column(
        Integer, primary_key=True, autoincrement=True
    )
    request_id: Mapped[str] = mapped_column(
        String(36), nullable=False, index=True,
        comment="Caller-supplied UUID stored as string for SQLite compatibility"
    )
    user_id: Mapped[int] = mapped_column(
        Integer, nullable=False, index=True
    )
    product_name: Mapped[str] = mapped_column(
        String(200), nullable=False
    )
    feedback_text: Mapped[str] = mapped_column(
        Text, nullable=False
    )
    sentiment_label: Mapped[str] = mapped_column(
        String(20), nullable=False,
        comment="One of: positive, negative, neutral"
    )
    confidence_score: Mapped[float] = mapped_column(
        Float, nullable=False,
        comment="VADER-derived confidence in [0.0, 1.0]"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    def __repr__(self) -> str:
        return (
            f"<FeedbackRecord id={self.id} user={self.user_id!r} "
            f"label={self.sentiment_label!r} confidence={self.confidence_score:.4f}>"
        )
