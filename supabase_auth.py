"""
InvestIQ Phase 2 - Supabase Auth Verification

Supabase handles signup, login, and password storage entirely on its own
(via Supabase Auth, called directly from the Next.js frontend using
@supabase/supabase-js). This backend never sees a password - it only
verifies the JWT that Supabase already issued, to identify which user is
making a request.

Uses Supabase's legacy shared-secret (HS256) JWT verification, found in
your Supabase dashboard under Settings > API > JWT Secret. This method is
simpler to set up but Supabase's own docs note it's being superseded by
asymmetric (JWKS-based) signing keys - see:
https://supabase.com/docs/guides/auth/signing-keys

UPGRADE PATH (when ready for production hardening): switch to fetching
Supabase's public keys from https://<project-ref>.supabase.co/auth/v1/jwks
and verify with those instead of a shared secret - removes the need to
store any secret in this backend at all, and matches Supabase's current
recommended approach. Not implemented here to avoid shipping unverified
code; the HS256 path below is fully tested against real Supabase-shaped
tokens (see test_supabase_auth.py).

Requires in .env:
    SUPABASE_JWT_SECRET=<from Supabase dashboard > Settings > API > JWT Secret>
"""

import os
from dotenv import load_dotenv
from jose import jwt, JWTError
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

load_dotenv()

SUPABASE_JWT_SECRET = os.environ.get("SUPABASE_JWT_SECRET")
JWT_ALGORITHM = "HS256"

if not SUPABASE_JWT_SECRET:
    raise RuntimeError(
        "SUPABASE_JWT_SECRET not set in .env. Find it in your Supabase "
        "dashboard under Settings > API > JWT Secret."
    )

# tokenUrl here is informational only (Supabase issues tokens, not us) -
# it just tells FastAPI's docs UI where a token would normally come from.
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="https://your-project.supabase.co/auth/v1/token")


class AuthenticatedUser:
    """Minimal user identity extracted from a verified Supabase JWT."""
    def __init__(self, user_id: str, email: str | None = None):
        self.user_id = user_id
        self.email = email


def decode_supabase_token(token: str) -> AuthenticatedUser:
    """
    Verifies a Supabase-issued JWT and extracts the user's identity.
    Raises HTTPException(401) if the token is invalid, expired, or malformed.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(
            token,
            SUPABASE_JWT_SECRET,
            algorithms=[JWT_ALGORITHM],
            audience="authenticated",  # Supabase sets this audience on user session tokens
        )
    except JWTError:
        raise credentials_exception

    user_id = payload.get("sub")
    if user_id is None:
        raise credentials_exception

    return AuthenticatedUser(user_id=user_id, email=payload.get("email"))


def get_current_user(token: str = Depends(oauth2_scheme)) -> AuthenticatedUser:
    """FastAPI dependency - protects an endpoint, injects the authenticated user's identity."""
    return decode_supabase_token(token)