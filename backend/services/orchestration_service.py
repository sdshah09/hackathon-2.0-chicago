# pyright: reportMissingImports=false
"""
End-to-End Orchestration Service.
Coordinates file upload, extraction, RAG indexing, summary generation, and PDF creation.
"""

from __future__ import annotations

import asyncio
import time
import uuid
from typing import List, Optional

from ..utils.db import get_connection
from ..utils.s3_client import S3_BUCKET, upload_file
from . import summary_service, pdf_service


def create_summary_pdf_record(
    patient_id: int,
    specialist_type: str,
    file_ids: List[int],
) -> dict:
    """
    Create a summary PDF record in the database.
    
    Returns:
        Dictionary with summary PDF record data
    """
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO summary_pdfs (patient_id, specialist_type, file_ids, status)
                VALUES (%s, %s, %s, 'processing')
                RETURNING id, patient_id, specialist_type, status, created_at
                """,
                (patient_id, specialist_type, file_ids),
            )
            return cur.fetchone()


def update_summary_pdf_status(summary_id: int, status: str) -> None:
    """Update the status of a summary PDF record."""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                UPDATE summary_pdfs 
                SET status = %s, updated_at = NOW()
                WHERE id = %s
                """,
                (status, summary_id),
            )


def update_summary_pdf_s3_info(summary_id: int, s3_key: str, s3_url: str) -> None:
    """Update summary PDF record with S3 information."""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                UPDATE summary_pdfs 
                SET s3_bucket = %s, s3_key = %s, s3_url = %s, 
                    status = 'completed', updated_at = NOW()
                WHERE id = %s
                """,
                (S3_BUCKET, s3_key, s3_url, summary_id),
            )


def get_summary_pdf_by_id(summary_id: int) -> Optional[dict]:
    """Get summary PDF record by ID."""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT id, patient_id, specialist_type, s3_url, status, file_ids, created_at
                FROM summary_pdfs
                WHERE id = %s
                """,
                (summary_id,),
            )
            return cur.fetchone()


def get_latest_summary_pdf(patient_id: int, specialist_type: str) -> Optional[dict]:
    """Get the latest summary PDF for a patient and specialist type."""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT id, patient_id, specialist_type, s3_url, status, file_ids, created_at
                FROM summary_pdfs
                WHERE patient_id = %s AND specialist_type = %s
                ORDER BY created_at DESC
                LIMIT 1
                """,
                (patient_id, specialist_type),
            )
            return cur.fetchone()


async def wait_for_files_processing(file_ids: List[int], max_wait_seconds: int = 300) -> bool:
    """
    Wait for all files to complete processing (upload + extraction).
    
    Args:
        file_ids: List of file IDs to wait for
        max_wait_seconds: Maximum time to wait (default 5 minutes)
    
    Returns:
        True if all files completed, False if timeout
    """
    from ..utils.db import get_connection
    
    start_time = time.time()
    
    while True:
        # Check elapsed time
        elapsed = time.time() - start_time
        if elapsed > max_wait_seconds:
            print(f"Timeout waiting for files {file_ids} to process")
            return False
        
        # Check file statuses
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT id, upload_status, extraction_status
                    FROM files
                    WHERE id = ANY(%s)
                    """,
                    (file_ids,),
                )
                files = cur.fetchall()
        
        # Check if all files are completed
        all_completed = True
        for file in files:
            if file["upload_status"] != "completed" or file["extraction_status"] != "completed":
                all_completed = False
                break
        
        if all_completed:
            print(f"All files {file_ids} completed processing")
            return True
        
        # Wait before checking again
        await asyncio.sleep(5)  # Check every 5 seconds


def _generate_s3_key_for_summary(patient_id: int, summary_id: int, specialist_type: str) -> str:
    """Generate S3 key for summary PDF."""
    unique_id = str(uuid.uuid4())[:8]
    return f"summaries/{patient_id}/{specialist_type}_{summary_id}_{unique_id}.pdf"


async def process_end_to_end_pipeline(
    patient_id: int,
    file_ids: List[int],
    specialist_type: str,
    summary_id: int,
    custom_prompt: Optional[str] = None,
) -> dict:
    """
    End-to-end processing pipeline:
    1. Wait for all files to be processed (upload + extraction)
    2. Generate summary using Pathway RAG
    3. Create PDF from summary
    4. Upload PDF to S3
    5. Update database with PDF link
    
    Args:
        patient_id: Patient/user ID
        file_ids: List of file IDs that were uploaded
        specialist_type: Type of specialist for summary
        summary_id: Summary PDF record ID
        custom_prompt: Optional custom prompt for summary generation
    
    Returns:
        Dictionary with summary PDF S3 URL and status
    """
    try:
        # Step 1: Wait for all files to be processed
        print(f"Waiting for files {file_ids} to complete processing...")
        files_ready = await wait_for_files_processing(file_ids, max_wait_seconds=300)
        
        if not files_ready:
            update_summary_pdf_status(summary_id, "failed")
            return {
                "status": "failed",
                "error": "Files did not complete processing within timeout period",
            }
        
        # Step 2: Generate summary
        print(f"Generating summary for patient {patient_id}, specialist {specialist_type}...")
        summary_result = await summary_service.generate_patient_summary(
            patient_id=patient_id,
            specialist_type=specialist_type,
            custom_prompt=custom_prompt,
        )
        
        if not summary_result.get("summary"):
            update_summary_pdf_status(summary_id, "failed")
            return {
                "status": "failed",
                "error": "Failed to generate summary - no data found",
            }
        
        # Step 3: Get patient name for PDF header
        from ..utils.db import get_connection
        patient_name = None
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT full_name FROM users WHERE id = %s", (patient_id,))
                row = cur.fetchone()
                if row:
                    patient_name = row["full_name"]
        
        # Step 4: Generate PDF
        print(f"Generating PDF for summary {summary_id}...")
        pdf_bytes = pdf_service.generate_summary_pdf(
            summary_text=summary_result["summary"],
            patient_name=patient_name,
            specialist_type=specialist_type,
        )
        
        # Step 5: Upload PDF to S3
        print(f"Uploading PDF to S3 for summary {summary_id}...")
        s3_key = _generate_s3_key_for_summary(patient_id, summary_id, specialist_type)
        
        # Upload in thread pool (S3 upload is blocking)
        loop = asyncio.get_event_loop()
        from concurrent.futures import ThreadPoolExecutor
        executor = ThreadPoolExecutor(max_workers=2)
        
        s3_url = await loop.run_in_executor(
            executor,
            upload_file,
            pdf_bytes,
            s3_key,
            "application/pdf",
            {
                "patient_id": str(patient_id),
                "summary_id": str(summary_id),
                "specialist_type": specialist_type,
            },
        )
        
        # Step 6: Update database with S3 info
        update_summary_pdf_s3_info(summary_id, s3_key, s3_url)
        
        print(f"✅ Summary PDF {summary_id} completed: {s3_url}")
        
        return {
            "status": "completed",
            "summary_id": summary_id,
            "s3_url": s3_url,
            "specialist_type": specialist_type,
        }
    
    except Exception as e:
        print(f"❌ Error in end-to-end pipeline for summary {summary_id}: {e}")
        update_summary_pdf_status(summary_id, "failed")
        return {
            "status": "failed",
            "error": str(e),
        }

