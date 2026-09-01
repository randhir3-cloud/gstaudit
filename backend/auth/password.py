"""Password hashing and policy validation."""

from __future__ import annotations

import re
from typing import List

import bcrypt

from models.security import PasswordPolicy


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))
    except Exception:
        return False


def validate_password(password: str, policy: PasswordPolicy, history_hashes: List[str] | None = None) -> None:
    errors: list[str] = []
    if len(password) < policy.min_length:
        errors.append(f"Password must be at least {policy.min_length} characters")
    if policy.require_uppercase and not re.search(r"[A-Z]", password):
        errors.append("Password must contain an uppercase letter")
    if policy.require_lowercase and not re.search(r"[a-z]", password):
        errors.append("Password must contain a lowercase letter")
    if policy.require_digit and not re.search(r"\d", password):
        errors.append("Password must contain a digit")
    if policy.require_special and not re.search(r"[^A-Za-z0-9]", password):
        errors.append("Password must contain a special character")
    if history_hashes:
        for old in history_hashes[: policy.history_count]:
            if verify_password(password, old):
                errors.append("Password was used recently")
                break
    if errors:
        raise ValueError("; ".join(errors))
