"""
routers/feedback.py — Route handlers for the Feedback API.

Endpoints:
    POST /feedback          Submit feedback text → VADER analysis → DB persist → return result
    GET  /feedback/{user_id} Retrieve all feedback records for a user

Both handlers:
    - Set request.state.request_id so the middleware END log and metrics CSV
      can carry the caller-supplied UUID.
    - Set request_id_ctx ContextVar so that log lines emitted *within* the
      handler (via the logging Filter) show the correct request_id.
    - Return the universal APIResponse[T] envelope.
"""

import logging

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

from auth import verify_token
from config import STATUS_MESSAGES
from context import request_id_ctx
from database import get_db
from exceptions import SentimentAnalysisError  # noqa: F401 — re-raised, not caught here
from models import FeedbackRecord
from schemas import (
    APIResponse,
    FeedbackListResponse,
    FeedbackRequest,
    FeedbackResponse,
)
from sentiment import analyze

logger = logging.getLogger("feedback_api")

router = APIRouter(prefix="/feedback", tags=["Feedback"])


# ── Dependency: get the shared VADER analyzer from app state ─────────────────────

def get_analyzer(request: Request) -> SentimentIntensityAnalyzer:
    """
    Provides the singleton VADER analyzer initialised during application startup.
    Never creates a new instance — always returns app.state.vader.
    """
    return request.app.state.vader


# ── POST /feedback ───────────────────────────────────────────────────────────────

@router.post(
    "",
    status_code=201,
    response_model=APIResponse[FeedbackResponse],
    summary="Submit product feedback for sentiment analysis",
)
def submit_feedback(
    request: Request,
    body: FeedbackRequest,
    db: Session = Depends(get_db),
    analyzer: SentimentIntensityAnalyzer = Depends(get_analyzer),
    _: None = Depends(verify_token),
) -> APIResponse[FeedbackResponse]:
    """
    Accept product feedback, run VADER sentiment analysis, persist the result,
    and return it wrapped in the standard APIResponse envelope.

    The caller must supply a UUID as request_id for end-to-end tracing.
    """
    # ── Set request_id for tracing ────────────────────────────────────────────────
    rid = str(body.request_id)
    request_id_ctx.set(rid)          # For log lines emitted within this handler
    request.state.request_id = rid   # For middleware END log and metrics CSV

    logger.debug(
        f"Feedback submission received | user={body.user_id!r} "
        f"product={body.product_name!r} text_len={len(body.feedback_text)}"
    )

    # ── Sentiment analysis ────────────────────────────────────────────────────────
    # analyze() raises SentimentAnalysisError if VADER fails → handled globally
    result = analyze(body.feedback_text, analyzer)
    logger.debug(
        f"Sentiment result | label={result.label} confidence={result.confidence_score}"
    )

    # ── Persist to database ───────────────────────────────────────────────────────
    record = FeedbackRecord(
        request_id=rid,
        user_id=body.user_id,
        product_name=body.product_name,
        feedback_text=body.feedback_text,
        sentiment_label=result.label,
        confidence_score=result.confidence_score,
    )
    try:
        db.add(record)
        db.commit()
        db.refresh(record)
        logger.debug(f"DB record inserted | id={record.id}")
    except Exception as exc:
        db.rollback()
        logger.error(f"DB insert failed: {exc}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to store feedback record")

    # ── Expose sentiment data to middleware for metrics CSV ───────────────────────
    request.state.sentiment_label = result.label
    request.state.confidence_score = result.confidence_score

    return APIResponse(
        success=True,
        status_code=201,
        message=STATUS_MESSAGES[201],
        data=FeedbackResponse.model_validate(record),
    )


# ── GET /feedback/{user_id} ──────────────────────────────────────────────────────

@router.get(
    "/{user_id}",
    status_code=200,
    response_model=APIResponse[FeedbackListResponse],
    summary="Retrieve all feedback records for a user",
)
def get_feedback(
    user_id: int,
    request_id: str,          # query parameter: ?request_id=<uuid>
    request: Request,
    db: Session = Depends(get_db),
    _: None = Depends(verify_token),
) -> APIResponse[FeedbackListResponse]:
    """
    Return all feedback records submitted by *user_id*.

    If the user has no records, returns a 200 with an empty list —
    not a 404, because an empty list is a valid state, not an error.

    The caller must supply a UUID as the ?request_id= query parameter.
    """
    # ── Set request_id for tracing ────────────────────────────────────────────────
    request_id_ctx.set(request_id)
    request.state.request_id = request_id

    logger.debug(f"Fetching feedback records | user={user_id!r}")

    # ── Query database ────────────────────────────────────────────────────────────
    try:
        records = (
            db.query(FeedbackRecord)
            .filter(FeedbackRecord.user_id == user_id)
            .order_by(FeedbackRecord.created_at.desc())
            .all()
        )
        logger.debug(f"DB query returned {len(records)} record(s) | user={user_id!r}")
    except Exception as exc:
        logger.error(f"DB query failed: {exc}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to retrieve feedback records")

    try:
        feedbacks = [FeedbackResponse.model_validate(r) for r in records]
    except Exception as exc:
        logger.error(
            f"Failed to serialise DB records for user={user_id!r}: {exc}",
            exc_info=True,
        )
        raise HTTPException(status_code=500, detail="Failed to process feedback records")

    return APIResponse(
        success=True,
        status_code=200,
        message=STATUS_MESSAGES[200],
        data=FeedbackListResponse(
            user_id=user_id,
            total=len(feedbacks),
            feedbacks=feedbacks,
        ),
    )
