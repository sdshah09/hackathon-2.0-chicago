# pyright: reportMissingImports=false
"""File upload and management service."""

from __future__ import annotations

import os
import uuid
from concurrent.futures import ThreadPoolExecutor
from typing import Optional

from ..utils.db import get_connection
from ..utils.s3_client import S3_BUCKET, upload_file

# Thread pool for async S3 uploads (limit concurrent uploads)
executor = ThreadPoolExecutor(max_workers=5)


def create_file_record(
    patient_id: int, filename: str, file_type: str, file_size: int
) -> dict:
    """
    Create a file record in the database immediately.
    Returns the created file record with id.

    Args:
        patient_id: ID of the patient/user
        filename: Original filename
        file_type: File type (jpeg, png, pdf)
        file_size: File size in bytes

    Returns:
        Dictionary with file record data
    """
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO files (patient_id, filename, file_type, file_size, upload_status)
                VALUES (%s, %s, %s, %s, 'pending')
                RETURNING id, filename, file_type, file_size, upload_status, created_at
                """,
                (patient_id, filename, file_type, file_size),
            )
            return cur.fetchone()


def update_file_upload_status(file_id: int, status: str) -> None:
    """Update the upload status of a file record."""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                UPDATE files 
                SET upload_status = %s, updated_at = NOW()
                WHERE id = %s
                """,
                (status, file_id),
            )


def update_file_s3_info(file_id: int, s3_key: str, s3_url: str) -> None:
    """Update file record with S3 information after successful upload."""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                UPDATE files 
                SET s3_bucket = %s, s3_key = %s, s3_url = %s, 
                    upload_status = 'completed', updated_at = NOW()
                WHERE id = %s
                """,
                (S3_BUCKET, s3_key, s3_url, file_id),
            )


def _generate_s3_key(patient_id: int, file_id: int, filename: str) -> str:
    """
    Generate a unique S3 key for storing the file.
    Format: patients/{patient_id}/{file_id}_{uuid}.{ext}
    """
    file_ext = filename.split(".")[-1].lower()
    unique_id = str(uuid.uuid4())[:8]  # Short UUID for readability
    return f"patients/{patient_id}/{file_id}_{unique_id}.{file_ext}"


def _normalize_file_type(content_type: str) -> str:
    """Convert MIME type to simple file type."""
    type_mapping = {
        "image/jpeg": "jpeg",
        "image/jpg": "jpeg",
        "image/png": "png",
        "application/pdf": "pdf",
    }
    return type_mapping.get(content_type.lower(), "unknown")


async def upload_file_to_s3_async(
    file_content: bytes,
    filename: str,
    content_type: str,
    file_id: int,
    patient_id: int,
) -> None:
    """
    Asynchronously upload a file to S3 using thread pool executor.
    Updates database with S3 info on success, or marks as failed on error.

    Args:
        file_content: Binary content of the file
        filename: Original filename
        content_type: MIME type of the file
        file_id: Database ID of the file record
        patient_id: ID of the patient/user
    """
    import asyncio

    # Update status to uploading
    update_file_upload_status(file_id, "uploading")

    try:
        # Generate S3 key
        s3_key = _generate_s3_key(patient_id, file_id, filename)

        # Upload to S3 in thread pool (non-blocking)
        loop = asyncio.get_event_loop()
        s3_url = await loop.run_in_executor(
            executor,
            upload_file,
            file_content,
            s3_key,
            content_type,
            {"patient_id": str(patient_id), "file_id": str(file_id)},
        )

        # Update database with S3 info
        update_file_s3_info(file_id, s3_key, s3_url)

        # Trigger text extraction asynchronously (runs in parallel, doesn't block)
        # Extraction happens independently after upload completes
        from . import extraction_service

        # Schedule extraction task (fire and forget - runs independently)
        # Get the current event loop and create task
        try:
            loop = asyncio.get_event_loop()
            loop.create_task(
                extraction_service.extract_text_from_file(
                    file_id=file_id,
                    s3_key=s3_key,
                    file_type=_normalize_file_type(content_type),
                )
            )
        except RuntimeError:
            # If no event loop is running, create a new one
            asyncio.ensure_future(
                extraction_service.extract_text_from_file(
                    file_id=file_id,
                    s3_key=s3_key,
                    file_type=_normalize_file_type(content_type),
                )
            )

    except Exception as e:
        # Mark as failed in database
        update_file_upload_status(file_id, "failed")
        # Log error (in production, use proper logging)
        print(f"Failed to upload file {file_id} to S3: {e}")
        raise


def get_file_by_id(file_id: int) -> Optional[dict]:
    """Get file record by ID."""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT id, patient_id, filename, file_type, file_size,
                       s3_bucket, s3_key, s3_url, upload_status, extraction_status,
                       created_at, updated_at
                FROM files
                WHERE id = %s
                """,
                (file_id,),
            )
            return cur.fetchone()


def get_patient_files(patient_id: int) -> list[dict]:
    """Get all files for a patient."""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT id, filename, file_type, file_size, s3_url,
                       upload_status, extraction_status, created_at
                FROM files
                WHERE patient_id = %s
                ORDER BY created_at DESC
                """,
                (patient_id,),
            )
            return cur.fetchall()

