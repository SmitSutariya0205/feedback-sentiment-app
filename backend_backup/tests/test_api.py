"""
tests/test_api.py — Comprehensive tests for the Feedback Sentiment API.

Covers all 10 scenario categories:
    1.  Successful POST /feedback
    2.  Successful GET  /feedback/{user_id}
    3.  Authentication failure (missing / wrong token)
    4.  Pydantic request validation failure (bad body / bad query params)
    5.  Resource-not-found case  (unknown user → 200 empty list per design)
    6.  DB failure on INSERT (POST)  and  DB failure on SELECT (GET)
    7.  Sentiment-analysis failure (VADER raises at runtime)
    8.  Unexpected / generic application failure
    9.  Response-model construction failure (ValidationError during serialisation)
    10. Metrics / CSV write failure

Design rules:
    - NO changes to application code.
    - Failures are injected via FastAPI dependency overrides and unittest.mock.patch.
    - Every test inspects the full APIResponse envelope structure.
    - Logging and request_id tracing are verified where observable.
"""

import logging
import uuid
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

# ── App imports ─────────────────────────────────────────────────────────────────
from database import Base, get_db
from main import app

# ── Constants ────────────────────────────────────────────────────────────────────

VALID_TOKEN = "dev-secret-token"
AUTH_HEADERS = {"Authorization": f"Bearer {VALID_TOKEN}"}
BAD_AUTH_HEADERS = {"Authorization": "Bearer wrong-token"}

# Fixed UUIDs used as request_ids throughout tests (makes log assertions easy)
RID_POST = "550e8400-e29b-41d4-a716-446655440099"
RID_GET = "6ba7b810-9dad-11d1-80b4-00c04fd430c8"

VALID_BODY = {
    "request_id": RID_POST,
    "user_id": 1,
    "product_name": "Widget Pro",
    "feedback_text": "This product is absolutely fantastic and I love it!",
}


# ── Fixtures ─────────────────────────────────────────────────────────────────────

@pytest.fixture(scope="module")
def in_memory_db():
    """
    SQLAlchemy engine backed by an in-memory SQLite database.
    Tables are created once per module; dropped after all tests in module finish.
    """
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    yield TestingSessionLocal
    Base.metadata.drop_all(bind=engine)


@pytest.fixture()
def client(in_memory_db):
    """
    TestClient with:
    - get_db overridden to in-memory SQLite (isolates tests from real feedback.db)
    - app.state.vader populated with a real VADER instance
    """
    from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

    def override_get_db():
        session = in_memory_db()
        try:
            yield session
        finally:
            session.rollback()
            session.close()

    app.dependency_overrides[get_db] = override_get_db
    app.state.vader = SentimentIntensityAnalyzer()

    with TestClient(app, raise_server_exceptions=False) as c:
        yield c

    app.dependency_overrides.clear()


# ── Helper ───────────────────────────────────────────────────────────────────────

def assert_envelope(body: dict, *, success: bool, status_code: int):
    """Assert the universal APIResponse envelope fields."""
    assert body["success"] is success, f"Expected success={success}, got {body['success']}"
    assert body["status_code"] == status_code, (
        f"Envelope status_code mismatch: expected {status_code}, got {body['status_code']}"
    )
    if success:
        assert body["error_message"] is None, "Successful response should have null error_message"
        assert body["data"] is not None, "Successful response should have non-null data"
    else:
        assert body["error_message"] is not None, "Error response should have non-null error_message"
        assert body["data"] is None, "Error response should have null data"


# ════════════════════════════════════════════════════════════════════════════════
# 1.  SUCCESSFUL POST /feedback
# ════════════════════════════════════════════════════════════════════════════════

class TestSuccessfulPost:
    def test_returns_201(self, client):
        r = client.post("/feedback", json=VALID_BODY, headers=AUTH_HEADERS)
        assert r.status_code == 201

    def test_envelope_structure(self, client):
        r = client.post("/feedback", json=VALID_BODY, headers=AUTH_HEADERS)
        assert_envelope(r.json(), success=True, status_code=201)

    def test_data_fields_present(self, client):
        r = client.post("/feedback", json=VALID_BODY, headers=AUTH_HEADERS)
        data = r.json()["data"]
        for field in ("id", "request_id", "user_id", "product_name",
                      "feedback_text", "sentiment_label", "confidence_score", "created_at"):
            assert field in data, f"Missing field '{field}' in response data"

    def test_request_id_echoed(self, client):
        r = client.post("/feedback", json=VALID_BODY, headers=AUTH_HEADERS)
        assert r.json()["data"]["request_id"] == RID_POST

    def test_sentiment_label_valid(self, client):
        r = client.post("/feedback", json=VALID_BODY, headers=AUTH_HEADERS)
        assert r.json()["data"]["sentiment_label"] in ("positive", "negative", "neutral")

    def test_confidence_score_in_range(self, client):
        r = client.post("/feedback", json=VALID_BODY, headers=AUTH_HEADERS)
        score = r.json()["data"]["confidence_score"]
        assert 0.0 <= score <= 1.0, f"confidence_score {score} out of [0, 1]"

    def test_positive_text_yields_positive_label(self, client):
        body = {**VALID_BODY, "request_id": str(uuid.uuid4()),
                "feedback_text": "Absolutely amazing! I love this product so much!"}
        r = client.post("/feedback", json=body, headers=AUTH_HEADERS)
        assert r.json()["data"]["sentiment_label"] == "positive"

    def test_negative_text_yields_negative_label(self, client):
        body = {**VALID_BODY, "request_id": str(uuid.uuid4()),
                "feedback_text": "Terrible, horrible, awful product. Complete waste of money."}
        r = client.post("/feedback", json=body, headers=AUTH_HEADERS)
        assert r.json()["data"]["sentiment_label"] == "negative"


# ════════════════════════════════════════════════════════════════════════════════
# 2.  SUCCESSFUL GET /feedback/{user_id}
# ════════════════════════════════════════════════════════════════════════════════

class TestSuccessfulGet:
    def _post_one(self, client, user_id: int = 42) -> dict:
        body = {**VALID_BODY, "request_id": str(uuid.uuid4()), "user_id": user_id}
        return client.post("/feedback", json=body, headers=AUTH_HEADERS).json()

    def test_returns_200(self, client):
        self._post_one(client, user_id=100)
        r = client.get(f"/feedback/100?request_id={RID_GET}", headers=AUTH_HEADERS)
        assert r.status_code == 200

    def test_envelope_structure(self, client):
        self._post_one(client, user_id=101)
        r = client.get(f"/feedback/101?request_id={RID_GET}", headers=AUTH_HEADERS)
        assert_envelope(r.json(), success=True, status_code=200)

    def test_data_fields_present(self, client):
        self._post_one(client, user_id=102)
        r = client.get(f"/feedback/102?request_id={RID_GET}", headers=AUTH_HEADERS)
        data = r.json()["data"]
        assert "user_id" in data
        assert "total" in data
        assert "feedbacks" in data

    def test_records_returned(self, client):
        self._post_one(client, user_id=103)
        r = client.get(f"/feedback/103?request_id={RID_GET}", headers=AUTH_HEADERS)
        data = r.json()["data"]
        assert data["total"] >= 1
        assert len(data["feedbacks"]) == data["total"]

    def test_user_id_matches(self, client):
        self._post_one(client, user_id=104)
        r = client.get(f"/feedback/104?request_id={RID_GET}", headers=AUTH_HEADERS)
        assert r.json()["data"]["user_id"] == 104


# ════════════════════════════════════════════════════════════════════════════════
# 3.  AUTHENTICATION FAILURE
# ════════════════════════════════════════════════════════════════════════════════

class TestAuthFailure:
    def test_missing_auth_header_returns_401(self, client):
        r = client.post("/feedback", json=VALID_BODY)
        assert r.status_code == 401

    def test_wrong_token_returns_401(self, client):
        r = client.post("/feedback", json=VALID_BODY, headers=BAD_AUTH_HEADERS)
        assert r.status_code == 401

    def test_missing_auth_envelope_structure(self, client):
        r = client.post("/feedback", json=VALID_BODY)
        assert_envelope(r.json(), success=False, status_code=401)

    def test_wrong_token_envelope_structure(self, client):
        r = client.post("/feedback", json=VALID_BODY, headers=BAD_AUTH_HEADERS)
        assert_envelope(r.json(), success=False, status_code=401)

    def test_error_message_present(self, client):
        r = client.post("/feedback", json=VALID_BODY)
        msg = r.json()["error_message"].lower()
        assert "bearer" in msg or "token" in msg

    def test_get_missing_auth_returns_401(self, client):
        r = client.get(f"/feedback/1?request_id={RID_GET}")
        assert r.status_code == 401

    def test_health_requires_no_auth(self, client):
        """Health endpoint must remain publicly accessible."""
        r = client.get("/health")
        assert r.status_code == 200


# ════════════════════════════════════════════════════════════════════════════════
# 4.  PYDANTIC VALIDATION FAILURE
# ════════════════════════════════════════════════════════════════════════════════

class TestValidationFailure:
    def test_missing_required_field_returns_422(self, client):
        body = {k: v for k, v in VALID_BODY.items() if k != "feedback_text"}
        r = client.post("/feedback", json=body, headers=AUTH_HEADERS)
        assert r.status_code == 422

    def test_feedback_text_too_short_returns_422(self, client):
        r = client.post("/feedback", json={**VALID_BODY, "feedback_text": "Hi"},
                        headers=AUTH_HEADERS)
        assert r.status_code == 422

    def test_feedback_text_too_long_returns_422(self, client):
        r = client.post("/feedback", json={**VALID_BODY, "feedback_text": "x" * 2001},
                        headers=AUTH_HEADERS)
        assert r.status_code == 422

    def test_invalid_request_id_returns_422(self, client):
        r = client.post("/feedback", json={**VALID_BODY, "request_id": "not-a-uuid"},
                        headers=AUTH_HEADERS)
        assert r.status_code == 422

    def test_user_id_zero_returns_422(self, client):
        r = client.post("/feedback", json={**VALID_BODY, "user_id": 0},
                        headers=AUTH_HEADERS)
        assert r.status_code == 422

    def test_user_id_negative_returns_422(self, client):
        r = client.post("/feedback", json={**VALID_BODY, "user_id": -5},
                        headers=AUTH_HEADERS)
        assert r.status_code == 422

    def test_user_id_string_on_get_returns_422(self, client):
        r = client.get(f"/feedback/not_an_int?request_id={RID_GET}", headers=AUTH_HEADERS)
        assert r.status_code == 422

    def test_missing_request_id_param_on_get_returns_422(self, client):
        r = client.get("/feedback/1", headers=AUTH_HEADERS)
        assert r.status_code == 422

    def test_validation_error_envelope_structure(self, client):
        body = {k: v for k, v in VALID_BODY.items() if k != "feedback_text"}
        r = client.post("/feedback", json=body, headers=AUTH_HEADERS)
        assert_envelope(r.json(), success=False, status_code=422)

    def test_validation_error_message_mentions_field(self, client):
        body = {k: v for k, v in VALID_BODY.items() if k != "feedback_text"}
        r = client.post("/feedback", json=body, headers=AUTH_HEADERS)
        assert "feedback_text" in r.json()["error_message"]

    def test_product_name_empty_returns_422(self, client):
        r = client.post("/feedback", json={**VALID_BODY, "product_name": ""},
                        headers=AUTH_HEADERS)
        assert r.status_code == 422


# ════════════════════════════════════════════════════════════════════════════════
# 5.  RESOURCE NOT FOUND / EMPTY LIST
# ════════════════════════════════════════════════════════════════════════════════

class TestResourceNotFound:
    def test_unknown_user_returns_200_not_404(self, client):
        """Per design: unknown user_id returns 200 with empty list, not 404."""
        r = client.get(f"/feedback/99999?request_id={RID_GET}", headers=AUTH_HEADERS)
        assert r.status_code == 200

    def test_unknown_user_returns_empty_list(self, client):
        r = client.get(f"/feedback/99999?request_id={RID_GET}", headers=AUTH_HEADERS)
        data = r.json()["data"]
        assert data["total"] == 0
        assert data["feedbacks"] == []

    def test_unknown_user_envelope_is_success(self, client):
        r = client.get(f"/feedback/99999?request_id={RID_GET}", headers=AUTH_HEADERS)
        assert_envelope(r.json(), success=True, status_code=200)

    def test_unknown_path_returns_404(self, client):
        """A completely unknown URL path returns 404 wrapped in our envelope."""
        r = client.get("/nonexistent", headers=AUTH_HEADERS)
        assert r.status_code == 404

    def test_unknown_path_envelope_structure(self, client):
        r = client.get("/nonexistent", headers=AUTH_HEADERS)
        assert_envelope(r.json(), success=False, status_code=404)

    def test_wrong_method_returns_405(self, client):
        """PUT on a defined path should return 405 Method Not Allowed."""
        r = client.put("/feedback", json=VALID_BODY, headers=AUTH_HEADERS)
        assert r.status_code == 405

    def test_wrong_method_envelope_structure(self, client):
        r = client.put("/feedback", json=VALID_BODY, headers=AUTH_HEADERS)
        assert_envelope(r.json(), success=False, status_code=405)


# ════════════════════════════════════════════════════════════════════════════════
# 6.  DATABASE FAILURE
# ════════════════════════════════════════════════════════════════════════════════

class TestDatabaseFailure:
    def _broken_insert_db(self):
        from sqlalchemy.exc import OperationalError
        session = MagicMock()
        session.add = MagicMock()
        session.commit = MagicMock(
            side_effect=OperationalError("disk I/O error", None, None)
        )
        session.rollback = MagicMock()
        session.refresh = MagicMock()

        def _override():
            yield session

        return _override

    def _broken_query_db(self):
        from sqlalchemy.exc import OperationalError
        session = MagicMock()
        q = MagicMock()
        q.filter.return_value = q
        q.order_by.return_value = q
        q.all.side_effect = OperationalError("table locked", None, None)
        session.query.return_value = q

        def _override():
            yield session

        return _override

    def test_db_insert_failure_returns_500(self, client):
        app.dependency_overrides[get_db] = self._broken_insert_db()
        try:
            r = client.post("/feedback", json=VALID_BODY, headers=AUTH_HEADERS)
            assert r.status_code == 500
        finally:
            app.dependency_overrides.pop(get_db, None)

    def test_db_insert_failure_envelope(self, client):
        app.dependency_overrides[get_db] = self._broken_insert_db()
        try:
            r = client.post("/feedback", json=VALID_BODY, headers=AUTH_HEADERS)
            assert_envelope(r.json(), success=False, status_code=500)
        finally:
            app.dependency_overrides.pop(get_db, None)

    def test_db_query_failure_on_get_returns_500(self, client):
        app.dependency_overrides[get_db] = self._broken_query_db()
        try:
            r = client.get(f"/feedback/1?request_id={RID_GET}", headers=AUTH_HEADERS)
            assert r.status_code == 500
        finally:
            app.dependency_overrides.pop(get_db, None)

    def test_db_query_failure_envelope(self, client):
        app.dependency_overrides[get_db] = self._broken_query_db()
        try:
            r = client.get(f"/feedback/1?request_id={RID_GET}", headers=AUTH_HEADERS)
            assert_envelope(r.json(), success=False, status_code=500)
        finally:
            app.dependency_overrides.pop(get_db, None)


# ════════════════════════════════════════════════════════════════════════════════
# 7.  SENTIMENT ANALYSIS FAILURE
# ════════════════════════════════════════════════════════════════════════════════

class TestSentimentFailure:
    def test_vader_failure_returns_500(self, client):
        """Simulate VADER raising SentimentAnalysisError at runtime."""
        with patch("routers.feedback.analyze") as mock_analyze:
            from exceptions import SentimentAnalysisError
            mock_analyze.side_effect = SentimentAnalysisError("VADER internal error")
            r = client.post("/feedback", json=VALID_BODY, headers=AUTH_HEADERS)
            assert r.status_code == 500

    def test_vader_failure_envelope(self, client):
        with patch("routers.feedback.analyze") as mock_analyze:
            from exceptions import SentimentAnalysisError
            mock_analyze.side_effect = SentimentAnalysisError("VADER internal error")
            r = client.post("/feedback", json=VALID_BODY, headers=AUTH_HEADERS)
            assert_envelope(r.json(), success=False, status_code=500)

    def test_vader_failure_error_message_is_not_empty(self, client):
        with patch("routers.feedback.analyze") as mock_analyze:
            from exceptions import SentimentAnalysisError
            mock_analyze.side_effect = SentimentAnalysisError("VADER internal error")
            r = client.post("/feedback", json=VALID_BODY, headers=AUTH_HEADERS)
            assert r.json()["error_message"]


# ════════════════════════════════════════════════════════════════════════════════
# 8.  UNEXPECTED / GENERIC APPLICATION FAILURE
# ════════════════════════════════════════════════════════════════════════════════

class TestUnexpectedFailure:
    def test_unexpected_exception_returns_500(self, client):
        with patch("routers.feedback.analyze") as mock_analyze:
            mock_analyze.side_effect = RuntimeError("something totally unexpected")
            r = client.post("/feedback", json=VALID_BODY, headers=AUTH_HEADERS)
            assert r.status_code == 500

    def test_unexpected_exception_envelope(self, client):
        with patch("routers.feedback.analyze") as mock_analyze:
            mock_analyze.side_effect = RuntimeError("something totally unexpected")
            r = client.post("/feedback", json=VALID_BODY, headers=AUTH_HEADERS)
            assert_envelope(r.json(), success=False, status_code=500)

    def test_unexpected_exception_does_not_leak_internals(self, client):
        """Raw exception details must not be surfaced to the client."""
        with patch("routers.feedback.analyze") as mock_analyze:
            mock_analyze.side_effect = RuntimeError("secret internal path /home/server/...")
            r = client.post("/feedback", json=VALID_BODY, headers=AUTH_HEADERS)
            # Generic handler returns a deliberately vague message
            assert "secret internal path" not in r.json().get("error_message", "")


# ════════════════════════════════════════════════════════════════════════════════
# 9.  RESPONSE-MODEL CONSTRUCTION FAILURE
# ════════════════════════════════════════════════════════════════════════════════

class TestResponseModelFailure:
    def test_serialisation_failure_on_get_returns_500(self, client):
        """
        Simulate FeedbackResponse.model_validate() raising while serialising
        DB records, to verify the try/except guard in the GET handler works.
        """
        # Insert a record so DB query returns something
        body = {**VALID_BODY, "request_id": str(uuid.uuid4()), "user_id": 200}
        client.post("/feedback", json=body, headers=AUTH_HEADERS)

        with patch("routers.feedback.FeedbackResponse.model_validate") as mock_v:
            mock_v.side_effect = Exception("model_validate failed: corrupt field")
            r = client.get(f"/feedback/200?request_id={RID_GET}", headers=AUTH_HEADERS)
            assert r.status_code == 500

    def test_serialisation_failure_envelope(self, client):
        body = {**VALID_BODY, "request_id": str(uuid.uuid4()), "user_id": 201}
        client.post("/feedback", json=body, headers=AUTH_HEADERS)

        with patch("routers.feedback.FeedbackResponse.model_validate") as mock_v:
            mock_v.side_effect = Exception("model_validate failed")
            r = client.get(f"/feedback/201?request_id={RID_GET}", headers=AUTH_HEADERS)
            assert_envelope(r.json(), success=False, status_code=500)


# ════════════════════════════════════════════════════════════════════════════════
# 10. METRICS / CSV WRITE FAILURE
# ════════════════════════════════════════════════════════════════════════════════

class TestMetricsFailure:
    def test_csv_write_failure_does_not_break_request(self, client):
        """
        If the CSV write fails, the primary request must still complete
        successfully. Failure is absorbed inside MetricsStore._append_csv_row().
        """
        with patch("builtins.open") as mock_open:
            mock_open.side_effect = OSError("Disk full")
            r = client.post("/feedback", json=VALID_BODY, headers=AUTH_HEADERS)
            assert r.status_code == 201

    def test_csv_write_failure_envelope_still_valid(self, client):
        with patch("builtins.open") as mock_open:
            mock_open.side_effect = OSError("Disk full")
            r = client.post("/feedback", json=VALID_BODY, headers=AUTH_HEADERS)
            assert_envelope(r.json(), success=True, status_code=201)

    def test_csv_stat_failure_does_not_break_request(self, client):
        """Simulate csv_path.stat() raising OSError (file locked on Windows)."""
        with patch("metrics.Path.stat") as mock_stat:
            mock_stat.side_effect = OSError("file locked")
            r = client.post("/feedback", json=VALID_BODY, headers=AUTH_HEADERS)
            assert r.status_code == 201

    def test_metrics_logged_when_csv_fails(self, client, caplog):
        """When CSV write fails, an ERROR must be logged by MetricsStore."""
        with caplog.at_level(logging.ERROR, logger="feedback_api"):
            with patch("builtins.open") as mock_open:
                mock_open.side_effect = OSError("Disk full — simulated")
                client.post("/feedback", json=VALID_BODY, headers=AUTH_HEADERS)

        error_msgs = [r.message for r in caplog.records if r.levelno == logging.ERROR]
        assert any("metrics" in m.lower() or "csv" in m.lower() for m in error_msgs), (
            f"Expected a metrics/CSV error log. Got: {error_msgs}"
        )


# ════════════════════════════════════════════════════════════════════════════════
# ENVELOPE CONSISTENCY CROSS-CHECK
# ════════════════════════════════════════════════════════════════════════════════

class TestEnvelopeConsistency:
    """Every response must have all 5 envelope keys, across all status codes."""
    REQUIRED_KEYS = {"success", "status_code", "message", "error_message", "data"}

    def _assert_all_keys(self, body: dict):
        missing = self.REQUIRED_KEYS - set(body.keys())
        assert not missing, f"Envelope missing keys: {missing}"

    def test_201_has_all_envelope_keys(self, client):
        r = client.post("/feedback", json=VALID_BODY, headers=AUTH_HEADERS)
        self._assert_all_keys(r.json())

    def test_200_has_all_envelope_keys(self, client):
        r = client.get(f"/feedback/99999?request_id={RID_GET}", headers=AUTH_HEADERS)
        self._assert_all_keys(r.json())

    def test_401_has_all_envelope_keys(self, client):
        r = client.post("/feedback", json=VALID_BODY)
        self._assert_all_keys(r.json())

    def test_422_has_all_envelope_keys(self, client):
        r = client.post("/feedback", json={}, headers=AUTH_HEADERS)
        self._assert_all_keys(r.json())

    def test_500_has_all_envelope_keys(self, client):
        with patch("routers.feedback.analyze") as mock_analyze:
            from exceptions import SentimentAnalysisError
            mock_analyze.side_effect = SentimentAnalysisError("boom")
            r = client.post("/feedback", json=VALID_BODY, headers=AUTH_HEADERS)
            self._assert_all_keys(r.json())

    def test_http_status_matches_envelope_status(self, client):
        """HTTP response status must always equal the envelope status_code field."""
        cases = [
            client.post("/feedback", json=VALID_BODY, headers=AUTH_HEADERS),
            client.get(f"/feedback/99999?request_id={RID_GET}", headers=AUTH_HEADERS),
            client.post("/feedback", json=VALID_BODY),
            client.post("/feedback", json={}, headers=AUTH_HEADERS),
        ]
        for resp in cases:
            body = resp.json()
            assert resp.status_code == body["status_code"], (
                f"HTTP {resp.status_code} but envelope.status_code={body['status_code']}"
            )
