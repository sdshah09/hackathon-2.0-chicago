# pyright: reportMissingImports=false
"""Authentication business logic backed by PostgreSQL."""

from __future__ import annotations

from typing import Optional

import bcrypt
from psycopg.errors import UniqueViolation

from .models import User
from .utils.db import get_connection


class AuthenticationError(Exception):
    """Base class for authentication failures."""


class InvalidCredentialsError(AuthenticationError):
    """Raised when username/password combination is invalid."""


class UserAlreadyExistsError(AuthenticationError):
    """Raised when attempting to register a duplicate username."""


def _hash_password(password: str) -> str:
    """Hash a password using bcrypt."""
    # Convert password to bytes and hash it
    password_bytes = password.encode('utf-8')
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password_bytes, salt)
    return hashed.decode('utf-8')


def _verify_password(password: str, hashed: str) -> bool:
    """Verify a password against a hash."""
    password_bytes = password.encode('utf-8')
    hashed_bytes = hashed.encode('utf-8')
    return bcrypt.checkpw(password_bytes, hashed_bytes)


def _row_to_user(row: dict) -> User:
    return User(
        id=row["id"],
        username=row["username"],
        full_name=row.get("full_name"),
        created_at=row.get("created_at"),
    )


def _normalize_username(username: str) -> str:
    return username.strip().lower()


def register_user(username: str, password: str, full_name: Optional[str] = None) -> User:
    """Create a new user record."""

    hashed_password = _hash_password(password)
    normalized_username = _normalize_username(username)

    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO users (username, full_name, password_hash)
                    VALUES (%s, %s, %s)
                    RETURNING id, username, full_name, created_at
                    """,
                    (normalized_username, full_name, hashed_password),
                )
                row = cur.fetchone()
    except UniqueViolation as exc:
        raise UserAlreadyExistsError("Username already exists") from exc

    if row is None:
        raise AuthenticationError("Failed to create user")
    return _row_to_user(row)


def authenticate_user(username: str, password: str) -> User:
    """Validate provided credentials and return the associated user."""

    normalized_username = _normalize_username(username)
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT id, username, full_name, password_hash, created_at
                FROM users
                WHERE username = %s
                """,
                (normalized_username,),
            )
            row = cur.fetchone()

    if not row:
        raise InvalidCredentialsError("Invalid username or password")

    if not _verify_password(password, row["password_hash"]):
        raise InvalidCredentialsError("Invalid username or password")

    return _row_to_user(row)

