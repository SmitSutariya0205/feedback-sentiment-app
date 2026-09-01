"""
metrics.py — Thread-safe in-memory metrics store with CSV persistence.

MetricsStore accumulates running aggregates for every authenticated request.
After each request, one row is appended to metrics.csv (append mode, growing history).

CSV columns:
    timestamp               UTC ISO timestamp of the request
    request_id              Caller-supplied UUID (or N/A for non-feedback requests)
    method                  HTTP method
    path                    Request path
    status_code             HTTP response status code
    execution_time_ms       End-to-end request time in milliseconds
    sentiment_label         Sentiment result (blank for non-POST-feedback requests)
    confidence_score        Confidence score  (blank for non-POST-feedback requests)
    total_requests          Cumulative request count at this point in time
    total_feedback_processed Cumulative POST /feedback successes
    avg_execution_time_ms   Running average execution time
    positive_count          Cumulative positive sentiment count
    negative_count          Cumulative negative sentiment count
    neutral_count           Cumulative neutral sentiment count
    avg_confidence_score    Running average confidence score across feedback requests
"""

import csv
import logging
import threading
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from config import METRICS_CSV_PATH

logger = logging.getLogger("feedback_api")

_CSV_HEADERS = [
    "timestamp",
    "request_id",
    "method",
    "path",
    "status_code",
    "execution_time_ms",
    "sentiment_label",
    "confidence_score",
    "total_requests",
    "total_feedback_processed",
    "avg_execution_time_ms",
    "positive_count",
    "negative_count",
    "neutral_count",
    "avg_confidence_score",
]


@dataclass
class MetricsStore:
    """
    Thread-safe in-memory metrics store.

    All mutations go through record_request(), which holds the lock for the
    entire update + CSV write to ensure the CSV row is consistent with the
    in-memory state.
    """

    total_requests: int = 0
    total_feedback_processed: int = 0
    total_execution_time_ms: float = 0.0
    positive_count: int = 0
    negative_count: int = 0
    neutral_count: int = 0
    total_confidence_sum: float = 0.0

    # Lock excluded from repr and equality checks
    _lock: threading.Lock = field(
        default_factory=threading.Lock, repr=False, compare=False
    )

    def record_request(
        self,
        *,
        request_id: str,
        method: str,
        path: str,
        status_code: int,
        execution_time_ms: float,
        sentiment_label: Optional[str] = None,
        confidence_score: Optional[float] = None,
    ) -> None:
        """
        Update all counters and append one row to metrics.csv.

        sentiment_label and confidence_score are None for non-feedback requests
        (e.g. GET /feedback). They are omitted from sentiment aggregates.
        """
        with self._lock:
            self.total_requests += 1
            self.total_execution_time_ms += execution_time_ms

            if sentiment_label is not None and confidence_score is not None:
                self.total_feedback_processed += 1
                self.total_confidence_sum += confidence_score
                if sentiment_label == "positive":
                    self.positive_count += 1
                elif sentiment_label == "negative":
                    self.negative_count += 1
                else:
                    self.neutral_count += 1

            avg_exec = self.total_execution_time_ms / self.total_requests
            avg_conf = (
                self.total_confidence_sum / self.total_feedback_processed
                if self.total_feedback_processed > 0
                else 0.0
            )

            self._append_csv_row(
                request_id=request_id,
                method=method,
                path=path,
                status_code=status_code,
                execution_time_ms=execution_time_ms,
                sentiment_label=sentiment_label,
                confidence_score=confidence_score,
                avg_exec=avg_exec,
                avg_conf=avg_conf,
            )

    def _append_csv_row(
        self,
        *,
        request_id: str,
        method: str,
        path: str,
        status_code: int,
        execution_time_ms: float,
        sentiment_label: Optional[str],
        confidence_score: Optional[float],
        avg_exec: float,
        avg_conf: float,
    ) -> None:
        """Write one row to metrics.csv. Creates the file with headers if absent."""
        csv_path = Path(METRICS_CSV_PATH)

        try:
            # Check inside the try so an OSError from stat() (e.g. file locked
            # on Windows between the exists() check and the open()) is also caught.
            needs_header = not csv_path.exists() or csv_path.stat().st_size == 0

            with open(csv_path, "a", newline="", encoding="utf-8") as fh:
                writer = csv.DictWriter(fh, fieldnames=_CSV_HEADERS)
                if needs_header:
                    writer.writeheader()
                writer.writerow(
                    {
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                        "request_id": request_id,
                        "method": method,
                        "path": path,
                        "status_code": status_code,
                        "execution_time_ms": round(execution_time_ms, 3),
                        "sentiment_label": sentiment_label or "",
                        "confidence_score": (
                            round(confidence_score, 4)
                            if confidence_score is not None
                            else ""
                        ),
                        "total_requests": self.total_requests,
                        "total_feedback_processed": self.total_feedback_processed,
                        "avg_execution_time_ms": round(avg_exec, 3),
                        "positive_count": self.positive_count,
                        "negative_count": self.negative_count,
                        "neutral_count": self.neutral_count,
                        "avg_confidence_score": round(avg_conf, 4),
                    }
                )
            logger.debug(f"Metrics row appended to {METRICS_CSV_PATH}")
        except Exception as exc:
            # Log the failure but do not raise — a metrics write error must never
            # break the primary request flow.
            logger.error(f"Failed to write metrics CSV: {exc}")


# Module-level singleton — imported and used by CombinedMiddleware.
metrics_store = MetricsStore()
