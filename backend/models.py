"""Pydantic models and schemas for the backend service."""

from datetime import datetime
from typing import Dict, Optional

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


class FileRecord(BaseModel):
    """File record representation."""

    id: int
    patient_id: int
    filename: str
    file_type: str
    file_size: int
    s3_url: Optional[str] = None
    upload_status: str
    extraction_status: str
    created_at: Optional[datetime] = None


class FileUploadResponse(BaseModel):
    """Response after file upload request."""

    message: str
    files: list[FileRecord]


class RAGQueryRequest(BaseModel):
    """Request for RAG query."""

    query: str = Field(..., min_length=1, description="Question or query about patient records")
    top_k: int = Field(default=5, ge=1, le=20, description="Number of chunks to retrieve")


class Source(BaseModel):
    """Source document information."""

    filename: str
    file_id: int
    s3_url: Optional[str] = None
    chunk_index: int


class RAGQueryResponse(BaseModel):
    """Response from RAG query."""

    query: str
    answer: str
    sources: list[Source]
    num_chunks_found: int


class SummaryRequest(BaseModel):
    """Request for patient summary generation."""

    specialist_type: str = Field(
        default="general",
        description="Type of specialist (dermatologist, ophthalmologist, immunologist, neurologist, cardiologist, general)",
    )
    custom_query: Optional[str] = Field(
        default=None,
        description="Optional custom query to extract specific information",
    )
    custom_prompt: Optional[str] = Field(
        default=None,
        description="Optional custom prompt for summary generation (overrides specialist_type focus)",
    )


class SummaryResponse(BaseModel):
    """Response with patient health summary."""

    summary: str
    sections: Dict[str, str]
    sources: list[Source]
    specialist_type: str
    num_sources: int = 0
    note: Optional[str] = None


class SummaryPdfResponse(BaseModel):
    """Response with summary PDF information."""

    summary_id: int
    status: str  # 'processing', 'completed', 'failed'
    s3_url: Optional[str] = None
    specialist_type: str
    message: str
    created_at: Optional[datetime] = None

