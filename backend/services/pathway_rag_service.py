# pyright: reportMissingImports=false
"""
Pathway RAG service for document indexing and retrieval.
Simplified version for hackathon - stores chunks in memory for now.
Can be extended to full Pathway dataflow later.
"""

from __future__ import annotations

import os
from typing import Optional, List, Dict, Any
from collections import defaultdict

# In-memory document store (for hackathon - can be replaced with Pathway dataflow)
_document_chunks: List[Dict[str, Any]] = []
_rag_initialized = False


def initialize_pathway_rag(
    openai_api_key: Optional[str] = None,
) -> None:
    """
    Initialize Pathway RAG pipeline.
    
    For hackathon: Simple in-memory storage.
    For production: Would set up full Pathway dataflow with embeddings and vector index.
    
    Args:
        openai_api_key: OpenAI API key (or set OPENAI_API_KEY env var)
    """
    global _rag_initialized
    
    # Check if OpenAI key is available (needed for embeddings/LLM later)
    api_key = openai_api_key or os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("⚠️  Warning: OPENAI_API_KEY not set. RAG queries will be limited.")
    
    _rag_initialized = True
    print("✅ Pathway RAG service initialized (in-memory storage)")


def add_document_to_index(
    text_chunks: List[tuple[str, dict]],
    patient_id: int,
    file_id: int,
    filename: str,
    s3_url: Optional[str] = None,
) -> None:
    """
    Add parsed document chunks to Pathway index.
    
    For hackathon: Stores in memory.
    For production: Would add to Pathway dataflow with automatic embeddings.
    
    Args:
        text_chunks: List of (text, metadata) tuples from parser
        patient_id: Patient/user ID
        file_id: File ID
        filename: Original filename
        s3_url: S3 URL of the file (optional)
    """
    global _document_chunks
    
    if not _rag_initialized:
        initialize_pathway_rag()
    
    # Store chunks with metadata for retrieval
    for idx, (text, chunk_metadata) in enumerate(text_chunks):
        chunk_data = {
            'text': text,
            'patient_id': patient_id,
            'file_id': file_id,
            'filename': filename,
            'chunk_index': idx,
            's3_url': s3_url,
            'metadata': {**chunk_metadata},
        }
        _document_chunks.append(chunk_data)
    
    print(f"✅ Added {len(text_chunks)} chunks to index (total: {len(_document_chunks)} chunks)")


async def query_rag(
    query: str,
    patient_id: Optional[int] = None,
    top_k: int = 5,
) -> Dict[str, Any]:
    """
    Query RAG pipeline to retrieve relevant documents.
    
    For hackathon: Simple text matching.
    For production: Would use Pathway's vector search with embeddings.
    
    Args:
        query: User query/question
        patient_id: Optional patient ID to filter results
        top_k: Number of chunks to retrieve
    
    Returns:
        Dictionary with answer, sources, and retrieved chunks
    """
    if not _rag_initialized:
        initialize_pathway_rag()
    
    # Filter by patient_id if provided
    candidate_chunks = _document_chunks
    if patient_id is not None:
        candidate_chunks = [c for c in _document_chunks if c.get('patient_id') == patient_id]
    
    if not candidate_chunks:
        return {
            'query': query,
            'answer': "No documents found for this patient.",
            'sources': [],
            'retrieved_chunks': [],
        }
    
    # Simple text matching (for hackathon)
    # In production, would use vector similarity search
    query_lower = query.lower()
    scored_chunks = []
    
    for chunk in candidate_chunks:
        text = chunk['text'].lower()
        # Simple relevance score (word overlap)
        score = sum(1 for word in query_lower.split() if word in text)
        if score > 0:
            scored_chunks.append((score, chunk))
    
    # Sort by score and get top_k
    scored_chunks.sort(reverse=True, key=lambda x: x[0])
    top_chunks = [chunk for _, chunk in scored_chunks[:top_k]]
    
    # Combine retrieved text
    retrieved_text = "\n\n".join([chunk['text'] for chunk in top_chunks])
    
    # Generate answer with LLM (if available)
    answer = retrieved_text  # Placeholder - would use LLM in production
    
    # Get sources
    sources = [
        {
            'filename': chunk['filename'],
            'file_id': chunk['file_id'],
            's3_url': chunk.get('s3_url'),
            'chunk_index': chunk['chunk_index'],
        }
        for chunk in top_chunks
    ]
    
    return {
        'query': query,
        'answer': answer,
        'sources': sources,
        'retrieved_chunks': top_chunks,
        'num_chunks_found': len(scored_chunks),
    }


def get_patient_documents(patient_id: int) -> List[Dict[str, Any]]:
    """
    Get all documents for a patient.
    
    Args:
        patient_id: Patient/user ID
    
    Returns:
        List of document metadata
    """
    patient_chunks = [c for c in _document_chunks if c.get('patient_id') == patient_id]
    
    # Group by file_id
    files = defaultdict(list)
    for chunk in patient_chunks:
        files[chunk['file_id']].append(chunk)
    
    # Return file summaries
    file_list = []
    for file_id, chunks in files.items():
        file_list.append({
            'file_id': file_id,
            'filename': chunks[0]['filename'],
            's3_url': chunks[0].get('s3_url'),
            'num_chunks': len(chunks),
            'total_text_length': sum(len(c['text']) for c in chunks),
        })
    
    return file_list


def is_rag_available() -> bool:
    """Check if RAG service is available."""
    return _rag_initialized
