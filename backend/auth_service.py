# pyright: reportMissingImports=false
"""Authentication business logic backed by PostgreSQL."""

from __future__ import annotations

from typing import Optional

from passlib.context import CryptContext
from psycopg.errors import UniqueViolation

from .models import User
from .utils.db import get_connection


class AuthenticationError(Exception):
    """Base class for authentication failures."""


class InvalidCredentialsError(AuthenticationError):
    """Raised when username/password combination is invalid."""


class UserAlreadyExistsError(AuthenticationError):
    """Raised when attempting to register a duplicate username."""


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


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

    hashed_password = pwd_context.hash(password)
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

    if not pwd_context.verify(password, row["password_hash"]):
        raise InvalidCredentialsError("Invalid username or password")

    return _row_to_user(row)

