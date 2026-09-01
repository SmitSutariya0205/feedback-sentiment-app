"""
sentiment.py — VADER sentiment analysis wrapper.

The SentimentIntensityAnalyzer instance is NOT created here.
It is initialised once during application startup (lifespan in main.py),
stored in app.state.vader, and injected into route handlers via the
get_analyzer() FastAPI dependency. This module only contains pure analysis logic.

Confidence derivation from VADER compound score:
    compound ∈ [-1.0, 1.0]
    compound >=  0.05  → positive,  confidence = compound
    compound <= -0.05  → negative,  confidence = abs(compound)
    else               → neutral,   confidence = 1.0 - abs(compound)
"""

import logging
from dataclasses import dataclass

from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

from exceptions import SentimentAnalysisError

logger = logging.getLogger("feedback_api")

# Thresholds recommended by VADER authors
_POSITIVE_THRESHOLD = 0.05
_NEGATIVE_THRESHOLD = -0.05


@dataclass(frozen=True)
class SentimentResult:
    """Immutable result of a single VADER analysis."""

    label: str           # "positive" | "negative" | "neutral"
    confidence_score: float  # Derived confidence in [0.0, 1.0]


def analyze(text: str, analyzer: SentimentIntensityAnalyzer) -> SentimentResult:
    """
    Run VADER sentiment analysis on *text* using the provided *analyzer* instance.

    Args:
        text:     Raw feedback string (already validated by Pydantic, min 5 chars).
        analyzer: Shared SentimentIntensityAnalyzer injected from app.state.vader.

    Returns:
        SentimentResult with label and confidence_score.

    Raises:
        SentimentAnalysisError: If VADER raises any exception during scoring.
    """
    try:
        scores = analyzer.polarity_scores(text)
    except Exception as exc:
        raise SentimentAnalysisError(str(exc)) from exc

    compound: float = scores["compound"]

    if compound >= _POSITIVE_THRESHOLD:
        label = "positive"
        confidence = compound
    elif compound <= _NEGATIVE_THRESHOLD:
        label = "negative"
        confidence = abs(compound)
    else:
        label = "neutral"
        # Neutral confidence: how close to 0 the compound is (max = 1.0 when compound = 0)
        confidence = 1.0 - abs(compound)

    confidence = round(confidence, 4)

    logger.debug(
        f"VADER result | label={label} confidence={confidence} compound={compound:.4f} "
        f"pos={scores['pos']:.4f} neu={scores['neu']:.4f} neg={scores['neg']:.4f}"
    )

    return SentimentResult(label=label, confidence_score=confidence)
