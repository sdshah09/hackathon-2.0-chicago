"""Pydantic models and schemas for the backend service."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class SignupRequest(BaseModel):
    """Payload for registering a new user."""

    username: str = Field(..., min_length=3, max_length=64)
    password: str = Field(..., min_length=6, max_length=128)
    full_name: Optional[str] = Field(default=None, max_length=128)


class SigninRequest(BaseModel):
    """Payload for authenticating an existing user."""

    username: str
    password: str


class User(BaseModel):
    """User representation returned to clients."""

    id: int
    username: str
    full_name: Optional[str] = None
    created_at: Optional[datetime] = None


class AuthResponse(BaseModel):
    """Standard response for signup/signin APIs."""

    message: str
    user: Optional[User] = None

