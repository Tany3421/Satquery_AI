"""
backend/auth_jwt.py
Standard JWT (JSON Web Token - HS256) implementation for SatQuery AI.

Enables secure stateless user authentication with zero external package dependencies.
Compatible with standard HS256 signature verification.
"""

import base64
import hmac
import hashlib
import json
import os
import time
from typing import Any, Dict, Optional


JWT_SECRET = os.getenv("JWT_SECRET", "satquery-jwt-secret-key-sih26167-2026")
JWT_ALGORITHM = "HS256"
DEFAULT_EXPIRY_SECONDS = 7 * 24 * 3600  # 7 days


def _b64url_encode(data: bytes) -> str:
    """Encodes bytes into URL-safe base64 string without trailing padding."""
    return base64.urlsafe_b64encode(data).decode("utf-8").rstrip("=")


def _b64url_decode(s: str) -> bytes:
    """Decodes URL-safe base64 string adding back any missing padding."""
    padded = s + "=" * (-len(s) % 4)
    return base64.urlsafe_b64decode(padded.encode("utf-8"))


def make_token(user: Dict[str, Any], expires_in: int = DEFAULT_EXPIRY_SECONDS) -> str:
    """
    Creates a signed JWT token for the authenticated user.
    Claims: id, username, role, exp, iat
    """
    now = int(time.time())
    header = {"alg": JWT_ALGORITHM, "typ": "JWT"}
    payload = {
        "id": str(user.get("id", "")),
        "username": user.get("username", ""),
        "role": user.get("role", "researcher"),
        "iat": now,
        "exp": now + expires_in,
    }

    header_b64 = _b64url_encode(json.dumps(header, separators=(",", ":")).encode("utf-8"))
    payload_b64 = _b64url_encode(json.dumps(payload, separators=(",", ":")).encode("utf-8"))

    msg = f"{header_b64}.{payload_b64}".encode("utf-8")
    signature = hmac.new(JWT_SECRET.encode("utf-8"), msg, hashlib.sha256).digest()
    sig_b64 = _b64url_encode(signature)

    return f"{header_b64}.{payload_b64}.{sig_b64}"


def verify_token(token: str) -> Optional[Dict[str, Any]]:
    """
    Verifies the JWT token signature and expiration.
    Returns decoded payload if valid, None otherwise.
    """
    if not token or not isinstance(token, str):
        return None

    # Strip 'Bearer ' if passed directly from Authorization header
    clean_token = token.strip()
    if clean_token.lower().startswith("bearer "):
        clean_token = clean_token[7:].strip()

    parts = clean_token.split(".")
    if len(parts) != 3:
        return None

    header_b64, payload_b64, sig_b64 = parts

    # 1. Verify Signature
    msg = f"{header_b64}.{payload_b64}".encode("utf-8")
    expected_sig = hmac.new(JWT_SECRET.encode("utf-8"), msg, hashlib.sha256).digest()

    try:
        actual_sig = _b64url_decode(sig_b64)
        if not hmac.compare_digest(expected_sig, actual_sig):
            return None
    except Exception:
        return None

    # 2. Decode and Validate Payload
    try:
        payload_bytes = _b64url_decode(payload_b64)
        payload = json.loads(payload_bytes.decode("utf-8"))
    except Exception:
        return None

    # 3. Check Expiry
    now = int(time.time())
    if payload.get("exp") and payload["exp"] < now:
        return None

    return payload


def safe_user(user: Dict[str, Any]) -> Dict[str, Any]:
    """Sanitizes user dictionary removing password hashes and salts."""
    return {
        "id": str(user.get("id", "")),
        "username": user.get("username", ""),
        "email": user.get("email", ""),
        "role": user.get("role", "researcher"),
        "created_at": user.get("created_at", ""),
    }
