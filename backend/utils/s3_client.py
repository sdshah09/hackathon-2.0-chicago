# pyright: reportMissingImports=false
"""AWS S3 client utilities for file operations."""

from __future__ import annotations

import os
from functools import lru_cache
from typing import BinaryIO

import boto3
from botocore.exceptions import ClientError


# S3 Configuration from environment variables
S3_BUCKET = os.getenv("S3_BUCKET", "patient-summary-files")
AWS_REGION = os.getenv("AWS_REGION", "us-east-1")
AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")


@lru_cache()
def get_s3_client():
    """
    Get a cached S3 client instance.
    Uses credentials from environment variables.
    """
    if not AWS_ACCESS_KEY_ID or not AWS_SECRET_ACCESS_KEY:
        raise RuntimeError(
            "AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY must be set in environment"
        )

    return boto3.client(
        "s3",
        aws_access_key_id=AWS_ACCESS_KEY_ID,
        aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
        region_name=AWS_REGION,
    )


def upload_file(
    file_content: bytes,
    s3_key: str,
    content_type: str | None = None,
    metadata: dict[str, str] | None = None,
) -> str:
    """
    Upload a file to S3.

    Args:
        file_content: Binary content of the file to upload
        s3_key: S3 object key (path) where file will be stored
        content_type: MIME type of the file (e.g., 'image/jpeg', 'application/pdf')
        metadata: Optional metadata dictionary to attach to the object

    Returns:
        S3 URL of the uploaded file

    Raises:
        ClientError: If upload fails
    """
    s3_client = get_s3_client()

    extra_args = {}
    if content_type:
        extra_args["ContentType"] = content_type
    if metadata:
        extra_args["Metadata"] = metadata

    try:
        s3_client.put_object(
            Bucket=S3_BUCKET,
            Key=s3_key,
            Body=file_content,
            **extra_args,
        )

        # Generate S3 URL
        s3_url = f"https://{S3_BUCKET}.s3.{AWS_REGION}.amazonaws.com/{s3_key}"
        return s3_url

    except ClientError as e:
        raise RuntimeError(f"Failed to upload file to S3: {e}") from e


def download_file(s3_key: str) -> bytes:
    """
    Download a file from S3.

    Args:
        s3_key: S3 object key (path) of the file to download

    Returns:
        Binary content of the file

    Raises:
        ClientError: If download fails
    """
    s3_client = get_s3_client()

    try:
        response = s3_client.get_object(Bucket=S3_BUCKET, Key=s3_key)
        return response["Body"].read()

    except ClientError as e:
        error_code = e.response.get("Error", {}).get("Code", "Unknown")
        if error_code == "NoSuchKey":
            raise FileNotFoundError(f"File not found in S3: {s3_key}") from e
        raise RuntimeError(f"Failed to download file from S3: {e}") from e


def delete_file(s3_key: str) -> None:
    """
    Delete a file from S3.

    Args:
        s3_key: S3 object key (path) of the file to delete

    Raises:
        ClientError: If deletion fails
    """
    s3_client = get_s3_client()

    try:
        s3_client.delete_object(Bucket=S3_BUCKET, Key=s3_key)

    except ClientError as e:
        raise RuntimeError(f"Failed to delete file from S3: {e}") from e


def file_exists(s3_key: str) -> bool:
    """
    Check if a file exists in S3.

    Args:
        s3_key: S3 object key (path) to check

    Returns:
        True if file exists, False otherwise
    """
    s3_client = get_s3_client()

    try:
        s3_client.head_object(Bucket=S3_BUCKET, Key=s3_key)
        return True
    except ClientError as e:
        error_code = e.response.get("Error", {}).get("Code", "Unknown")
        if error_code == "404":
            return False
        # Re-raise if it's a different error
        raise RuntimeError(f"Error checking file existence in S3: {e}") from e

