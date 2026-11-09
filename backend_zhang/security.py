"""Password security (isolated here; other modules must not implement their own hashing).

Scheme: secrets random salt + hashlib.pbkdf2_hmac key derivation +
hmac.compare_digest constant-time comparison. Plaintext passwords are never
written to disk or logs.
"""

from __future__ import annotations

import hashlib
import hmac
import secrets

from backend_zhang import config


def generate_salt() -> str:
    """Generate a random salt (hex string)."""
    return secrets.token_hex(config.SALT_BYTES)


def hash_password(password: str, salt: str) -> str:
    """Derive a password hash using PBKDF2-HMAC."""
    derived = hashlib.pbkdf2_hmac(
        config.PBKDF2_ALGORITHM,
        str(password).encode("utf-8"),
        str(salt).encode("utf-8"),
        config.PBKDF2_ITERATIONS,
    )
    return derived.hex()


def verify_password(password: str, salt: str, expected_hash: str) -> bool:
    """Verify a password against the stored hash (constant-time comparison)."""
    if not salt or not expected_hash:
        return False
    actual = hash_password(password, salt)
    return hmac.compare_digest(actual, str(expected_hash))
