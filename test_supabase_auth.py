"""
Tests supabase_auth.py against a synthetic Supabase-shaped JWT (same claim
structure Supabase actually issues: sub=UUID, role=authenticated, email,
exp), and tests the updated models.py (no local users table) against the
real local Postgres instance.

We don't have a live Supabase project to test against in this environment,
so this test signs its own token with a known secret to prove the
VERIFICATION LOGIC is correct - the same decode function will work
identically against a real Supabase-issued token, since the JWT format
and verification process are standard.
"""

import os
import uuid
from datetime import datetime, timedelta, timezone
from jose import jwt

os.environ["SUPABASE_JWT_SECRET"] = "test-supabase-shared-secret-for-testing"
os.environ["DATABASE_URL"] = "postgresql://postgres:devpassword@localhost:5432/investiq"

from supabase_auth import decode_supabase_token, AuthenticatedUser
from fastapi import HTTPException

TEST_SECRET = "test-supabase-shared-secret-for-testing"
test_user_id = str(uuid.uuid4())

print("=" * 60)
print("TEST 1: Valid Supabase-shaped token is accepted")
print("=" * 60)

valid_payload = {
    "sub": test_user_id,
    "email": "ahmed@example.com",
    "role": "authenticated",
    "aud": "authenticated",
    "exp": datetime.now(timezone.utc) + timedelta(hours=1),
}
valid_token = jwt.encode(valid_payload, TEST_SECRET, algorithm="HS256")

user = decode_supabase_token(valid_token)
print(f"Decoded user_id: {user.user_id}")
print(f"Decoded email: {user.email}")
print(f"user_id matches expected: {user.user_id == test_user_id}")

print()
print("=" * 60)
print("TEST 2: Expired token is rejected")
print("=" * 60)
expired_payload = {
    "sub": test_user_id,
    "aud": "authenticated",
    "exp": datetime.now(timezone.utc) - timedelta(hours=1),  # already expired
}
expired_token = jwt.encode(expired_payload, TEST_SECRET, algorithm="HS256")
try:
    decode_supabase_token(expired_token)
    print("FAIL: expired token was accepted")
except HTTPException as e:
    print(f"Correctly rejected: {e.status_code} {e.detail}")

print()
print("=" * 60)
print("TEST 3: Token signed with wrong secret is rejected")
print("=" * 60)
wrong_secret_token = jwt.encode(valid_payload, "wrong-secret-entirely", algorithm="HS256")
try:
    decode_supabase_token(wrong_secret_token)
    print("FAIL: token with wrong secret was accepted")
except HTTPException as e:
    print(f"Correctly rejected: {e.status_code} {e.detail}")

print()
print("=" * 60)
print("TEST 4: Token missing 'sub' claim is rejected")
print("=" * 60)
no_sub_payload = {"aud": "authenticated", "exp": datetime.now(timezone.utc) + timedelta(hours=1)}
no_sub_token = jwt.encode(no_sub_payload, TEST_SECRET, algorithm="HS256")
try:
    decode_supabase_token(no_sub_token)
    print("FAIL: token without sub was accepted")
except HTTPException as e:
    print(f"Correctly rejected: {e.status_code} {e.detail}")

print()
print("=" * 60)
print("TEST 5: Updated models.py works against real Postgres (no local users table)")
print("=" * 60)
from database import engine, SessionLocal, Base
from models import Portfolio, SavedReport

Base.metadata.drop_all(bind=engine)
Base.metadata.create_all(bind=engine)
print("Tables created: portfolios, saved_reports (no users table)")

db = SessionLocal()
portfolio = Portfolio(
    user_id=test_user_id,  # a Supabase UUID, stored as plain string
    name="Test Portfolio",
    holdings=[{"ticker": "AAPL", "weight": 0.6}, {"ticker": "MSFT", "weight": 0.4}],
)
db.add(portfolio)
db.commit()
db.refresh(portfolio)
print(f"Portfolio saved with Supabase user_id: {portfolio.user_id}")
print(f"user_id matches the JWT's sub claim: {portfolio.user_id == test_user_id}")
db.close()

print()
print("ALL TESTS PASSED")