# pyright: reportMissingImports=false
"""
Pathway service for document parsing and indexing.
Replaces custom OCR extraction with Pathway's built-in parsers.
"""

from __future__ import annotations

import asyncio
from concurrent.futures import ThreadPoolExecutor
from typing import Optional

try:
    from pathway.xpacks.llm.parsers import DoclingParser, PaddleOCRParser
except ImportError:
    DoclingParser = None  # type: ignore
    PaddleOCRParser = None  # type: ignore

# Thread pool for async Pathway operations
pathway_executor = ThreadPoolExecutor(max_workers=2)

# Module-level parser instances (expensive to create, reuse them)
_docling_parser: Optional[DoclingParser] = None
_paddleocr_parser: Optional[PaddleOCRParser] = None


def get_docling_parser() -> Optional[DoclingParser]:
    """Get or create a cached DoclingParser instance."""
    global _docling_parser
    
    if DoclingParser is None:
        return None
    
    if _docling_parser is None:
        try:
            _docling_parser = DoclingParser()
        except Exception as e:
            print(f"Warning: Failed to initialize DoclingParser: {e}")
            return None
    
    return _docling_parser


def get_paddleocr_parser() -> Optional[PaddleOCRParser]:
    """Get or create a cached PaddleOCRParser instance."""
    global _paddleocr_parser
    
    if PaddleOCRParser is None:
        return None
    
    if _paddleocr_parser is None:
        try:
            # Use regular PaddleOCR (PPStructureV3 requires extra dependencies)
            from paddleocr import PaddleOCR
            _paddleocr_parser = PaddleOCRParser(pipeline=PaddleOCR())
        except Exception as e:
            print(f"Warning: Failed to initialize PaddleOCRParser: {e}")
            return None
    
    return _paddleocr_parser


async def parse_file_with_pathway(
    file_content: bytes,
    file_type: str,
    filename: str,
    patient_id: int,
    file_id: int,
) -> dict:
    """
    Parse a file using Pathway parsers.
    
    Args:
        file_content: Binary content of the file
        file_type: Type of file (jpeg, png, pdf)
        filename: Original filename
        patient_id: Patient/user ID
        file_id: File ID
    
    Returns:
        Dictionary with parsed content and metadata
    """
    loop = asyncio.get_event_loop()
    
    # Choose parser based on file type
    if file_type == "pdf":
        # Try DoclingParser first (faster, no OCR needed for text PDFs)
        parser = get_docling_parser()
        if parser is None:
            # Fallback to PaddleOCRParser if DoclingParser not available
            parser = get_paddleocr_parser()
    else:
        # For images, use PaddleOCRParser
        parser = get_paddleocr_parser()
    
    if parser is None:
        raise RuntimeError(
            "No Pathway parser available. Install pathway[llm] and required dependencies."
        )
    
    # Parse file (Pathway parsers are async, so we can await directly)
    try:
        # Pathway parsers are async UDFs - call them directly
        parsed_result = await _parse_file_async(
            parser,
            file_content,
            filename,
            patient_id,
            file_id,
        )
        return parsed_result
    
    except Exception as e:
        raise RuntimeError(f"Failed to parse file with Pathway: {e}") from e


async def _parse_file_async(
    parser,
    file_content: bytes,
    filename: str,
    patient_id: int,
    file_id: int,
) -> dict:
    """
    Async parsing function (Pathway parsers are async UDFs).
    
    Args:
        parser: Pathway parser instance
        file_content: Binary content of the file
        filename: Original filename
        patient_id: Patient/user ID
        file_id: File ID
    
    Returns:
        Dictionary with parsed content
    """
    try:
        # Pathway parsers are async UDFs
        # DoclingParser has a parse() method, PaddleOCRParser uses __wrapped__()
        if hasattr(parser, 'parse'):
            # DoclingParser
            parsed_chunks = await parser.parse(file_content)
        else:
            # PaddleOCRParser (uses __wrapped__)
            parsed_chunks = await parser.__wrapped__(file_content)
        
        # Combine all text chunks
        extracted_text = "\n\n".join([chunk[0] for chunk in parsed_chunks if chunk[0]])
        
        # Combine metadata from all chunks
        all_metadata = {}
        if parsed_chunks:
            # Use metadata from first chunk as base
            all_metadata = parsed_chunks[0][1] if len(parsed_chunks[0]) > 1 else {}
        
        # Add our custom metadata
        all_metadata.update({
            'filename': filename,
            'patient_id': patient_id,
            'file_id': file_id,
            'parser': parser.__class__.__name__,
            'num_chunks': len(parsed_chunks),
        })
        
        return {
            'text': extracted_text,
            'metadata': all_metadata,
            'chunks': parsed_chunks,  # Keep chunks for potential future use
        }
    
    except Exception as e:
        raise RuntimeError(f"Pathway parsing failed: {e}") from e


def is_pathway_available() -> bool:
    """Check if Pathway parsers are available."""
    return (DoclingParser is not None) or (PaddleOCRParser is not None)

