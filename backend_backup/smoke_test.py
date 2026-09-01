"""
smoke_test.py — Automated smoke tests for the Feedback Sentiment API.
Run: python smoke_test.py
"""
import json
import urllib.error
import urllib.request

BASE = "http://127.0.0.1:8000"
TOKEN = "dev-secret-token"
AUTH_HEADERS = {"Authorization": f"Bearer {TOKEN}", "Content-Type": "application/json"}
NO_AUTH_HEADERS = {"Content-Type": "application/json"}

PASS_COUNT = 0
FAIL_COUNT = 0


def req(method, path, body=None, headers=None, expected_status=None):
    global PASS_COUNT, FAIL_COUNT
    h = headers if headers is not None else AUTH_HEADERS
    data = json.dumps(body).encode() if body else None
    r = urllib.request.Request(f"{BASE}{path}", data=data, headers=h, method=method)
    try:
        with urllib.request.urlopen(r) as resp:
            status = resp.status
            payload = json.loads(resp.read())
    except urllib.error.HTTPError as e:
        status = e.code
        payload = json.loads(e.read())
    ok = expected_status is None or status == expected_status
    mark = "PASS" if ok else "FAIL"
    if ok:
        PASS_COUNT += 1
    else:
        FAIL_COUNT += 1
    print(f"  [{mark}] {method} {path} -> {status}", end="")
    if not ok:
        print(f"  (expected {expected_status})")
        print(f"         {json.dumps(payload)[:200]}")
    else:
        print()
    return payload, status


print("\n=== Feedback Sentiment API — Smoke Tests ===\n")

# 1. Health check (no token)
print("1. GET /health — no auth required")
req("GET", "/health", headers={}, expected_status=200)

# 2. Valid feedback submission
print("2. POST /feedback — valid positive feedback")
body = {
    "request_id": "550e8400-e29b-41d4-a716-446655440000",
    "user_id": 42,
    "product_name": "Widget Pro",
    "feedback_text": "This product is absolutely fantastic, I love it!",
}
r, _ = req("POST", "/feedback", body=body, expected_status=201)
if r.get("data"):
    label = r["data"]["sentiment_label"]
    conf = r["data"]["confidence_score"]
    print(f"         sentiment={label}  confidence={conf}")

# 3. Invalid token
print("3. POST /feedback — invalid bearer token")
bad_auth = {"Authorization": "Bearer wrong-token", "Content-Type": "application/json"}
req("POST", "/feedback", body=body, headers=bad_auth, expected_status=401)

# 4. No token at all
print("4. POST /feedback — missing authorization header")
req("POST", "/feedback", body=body, headers={"Content-Type": "application/json"}, expected_status=401)

# 5. Feedback text too short (< 5 chars)
print("5. POST /feedback — feedback_text too short")
short = {**body, "request_id": "6ba7b810-9dad-11d1-80b4-00c04fd430c8", "feedback_text": "Bad"}
req("POST", "/feedback", body=short, expected_status=422)

# 6. Invalid UUID for request_id
print("6. POST /feedback — request_id not a UUID")
bad_uuid = {**body, "request_id": "not-a-uuid"}
req("POST", "/feedback", body=bad_uuid, expected_status=422)

# 7. Missing required field
print("7. POST /feedback — missing request_id field")
missing = {"user_id": 42, "product_name": "X", "feedback_text": "Great product indeed"}
req("POST", "/feedback", body=missing, expected_status=422)

# 8. Negative sentiment
print("8. POST /feedback — negative sentiment")
neg = {
    "request_id": "7c9e6679-7425-40de-944b-e07fc1f90ae7",
    "user_id": 42,
    "product_name": "Widget Pro",
    "feedback_text": "Terrible product, completely useless and totally broken!",
}
r2, _ = req("POST", "/feedback", body=neg, expected_status=201)
if r2.get("data"):
    print(f"         sentiment={r2['data']['sentiment_label']}  confidence={r2['data']['confidence_score']}")

# 9. Neutral sentiment
print("9. POST /feedback — neutral sentiment")
neutral = {
    "request_id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
    "user_id": 42,
    "product_name": "Widget Pro",
    "feedback_text": "The product exists and I received it.",
}
r3, _ = req("POST", "/feedback", body=neutral, expected_status=201)
if r3.get("data"):
    print(f"         sentiment={r3['data']['sentiment_label']}  confidence={r3['data']['confidence_score']}")

# 10. GET feedback for existing user
print("10. GET /feedback/42 — existing user")
r4, _ = req("GET", "/feedback/42?request_id=6ba7b810-9dad-11d1-80b4-00c04fd430c8", expected_status=200)
if r4.get("data"):
    print(f"         total={r4['data']['total']} records returned")

# 11. GET feedback for unknown user → 200 with empty list
print("11. GET /feedback/999 — empty list, not 404")
r5, _ = req("GET", "/feedback/999?request_id=6ba7b810-9dad-11d1-80b4-00c04fd430c8", expected_status=200)
if r5.get("data") is not None and r5["data"]["total"] == 0:
    print("         total=0 confirmed")
else:
    print(f"  [FAIL] Expected total=0, got: {r5}")

# 12. GET feedback — missing request_id param
print("12. GET /feedback/42 — missing ?request_id param")
req("GET", "/feedback/42", expected_status=422)

print(f"\n=== Results: {PASS_COUNT} passed, {FAIL_COUNT} failed ===\n")
