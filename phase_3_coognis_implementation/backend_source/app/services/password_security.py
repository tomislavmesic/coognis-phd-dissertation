from __future__ import annotations

import hashlib
import hmac
import secrets
from dataclasses import dataclass

from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerifyMismatchError

_password_hasher = PasswordHasher()


@dataclass
class PasswordVerificationResult:
    valid: bool
    needs_rehash: bool = False


def hash_password(password: str) -> str:
    return _password_hasher.hash(password)


def verify_password(password: str, stored_value: str) -> PasswordVerificationResult:
    if stored_value.startswith("$argon2"):
        try:
            valid = _password_hasher.verify(stored_value, password)
        except (VerifyMismatchError, InvalidHashError):
            return PasswordVerificationResult(valid=False, needs_rehash=False)
        return PasswordVerificationResult(valid=bool(valid), needs_rehash=_password_hasher.check_needs_rehash(stored_value))

    try:
        salt, expected = stored_value.split("$", 1)
    except ValueError:
        return PasswordVerificationResult(valid=False, needs_rehash=False)

    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt.encode("utf-8"), 100_000)
    is_valid = hmac.compare_digest(digest.hex(), expected)
    return PasswordVerificationResult(valid=is_valid, needs_rehash=is_valid)


def hash_password_legacy(password: str) -> str:
    salt = secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt.encode("utf-8"), 100_000)
    return f"{salt}${digest.hex()}"
