# pyright: reportMissingImports=false
"""Text extraction service using Pathway parsers (replaces custom OCR)."""

from __future__ import annotations

import asyncio
from concurrent.futures import ThreadPoolExecutor
from typing import Optional

# Thread pool for async extraction operations
extraction_executor = ThreadPoolExecutor(max_workers=3)


def update_extraction_status(file_id: int, status: str) -> None:
    """Update the extraction status of a file record."""
    from ..utils.db import get_connection

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                UPDATE files 
                SET extraction_status = %s, updated_at = NOW()
                WHERE id = %s
                """,
                (status, file_id),
            )


def save_extracted_text(file_id: int, extracted_text: str, metadata: Optional[dict] = None) -> None:
    """
    Save extracted text to database.
    TODO: Create extracted_texts table or add text column to files table.
    """
    from ..utils.db import get_connection

    # For now, just update status - will implement proper storage later
    with get_connection() as conn:
        with conn.cursor() as cur:
            # TODO: Store extracted_text in database
            # This is a placeholder - actual implementation will depend on schema
            cur.execute(
                """
                UPDATE files 
                SET extraction_status = 'completed', updated_at = NOW()
                WHERE id = %s
                """,
                (file_id,),
            )


async def extract_text_from_file(file_id: int, s3_key: str, file_type: str, patient_id: int, filename: str) -> None:
    """
    Extract text from a file asynchronously using Pathway parsers.
    
    Args:
        file_id: Database ID of the file
        s3_key: S3 key of the file to extract text from
        file_type: Type of file (jpeg, png, pdf)
        patient_id: Patient/user ID
        filename: Original filename
    """
    # Update status to processing
    update_extraction_status(file_id, "processing")

    try:
        # Download file from S3
        from ..utils.s3_client import download_file

        loop = asyncio.get_event_loop()
        file_content = await loop.run_in_executor(
            extraction_executor,
            download_file,
            s3_key,
        )

        # Use Pathway to parse the file
        from .pathway_service import parse_file_with_pathway
        
        parsed_result = await parse_file_with_pathway(
            file_content=file_content,
            file_type=file_type,
            filename=filename,
            patient_id=patient_id,
            file_id=file_id,
        )

        # Save extracted text to database
        extracted_text = parsed_result.get('text', '')
        chunks = parsed_result.get('chunks', [])
        metadata = parsed_result.get('metadata', {})
        
        save_extracted_text(file_id, extracted_text, metadata)
        
        # Index document in Pathway for RAG retrieval
        try:
            from .pathway_rag_service import add_document_to_index
            from ..utils.s3_client import get_file_url
            
            # Get S3 URL
            s3_url = get_file_url(s3_key) if s3_key else None
            
            # Add to Pathway index
            add_document_to_index(
                text_chunks=chunks,
                patient_id=patient_id,
                file_id=file_id,
                filename=filename,
                s3_url=s3_url,
            )
            print(f"✅ Indexed {len(chunks)} chunks in Pathway for file {file_id}")
        except Exception as e:
            # Don't fail extraction if indexing fails
            print(f"⚠️  Warning: Failed to index in Pathway: {e}")

        print(f"✅ Successfully extracted text from file {file_id} using Pathway")

    except Exception as e:
        # Mark extraction as failed
        update_extraction_status(file_id, "failed")
        print(f"❌ Failed to extract text from file {file_id}: {e}")
        raise


# Removed _perform_extraction - now using Pathway parsers directly

