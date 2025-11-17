# pyright: reportMissingImports=false
"""
Patient Summary Generation Service.
Generates 1-2 page health summaries for specialists using Pathway RAG + LLM.
"""

from __future__ import annotations

import os
from typing import Optional, List, Dict, Any

try:
    from pathway.xpacks.llm.llms import OpenAIChat
    import openai
except ImportError:
    OpenAIChat = None  # type: ignore
    openai = None  # type: ignore

# Specialist-specific information extraction prompts
SPECIALIST_PROMPTS = {
    "dermatologist": """
    Extract information relevant to dermatology:
    - Skin conditions, rashes, lesions
    - Dermatological diagnoses
    - Skin-related medications
    - Allergies (especially skin-related)
    - Recent skin procedures or treatments
    """,
    "ophthalmologist": """
    Extract information relevant to ophthalmology:
    - Eye conditions, vision problems
    - Eye-related diagnoses
    - Eye medications
    - Recent eye exams or procedures
    - Vision-related symptoms
    """,
    "immunologist": """
    Extract information relevant to immunology:
    - Allergies and allergic reactions
    - Immune system conditions
    - Immunosuppressant medications
    - Recent infections
    - Autoimmune conditions
    """,
    "neurologist": """
    Extract information relevant to neurology:
    - Neurological symptoms
    - Neurological diagnoses
    - Neurological medications
    - Headaches, seizures, cognitive issues
    - Recent neurological exams
    """,
    "cardiologist": """
    Extract information relevant to cardiology:
    - Heart conditions
    - Cardiovascular medications
    - Blood pressure readings
    - Cardiac test results
    - Heart-related symptoms
    """,
    "general": """
    Extract general medical information:
    - Active medications
    - Allergies
    - Recent diagnoses
    - Lab results
    - Current symptoms
    """,
}


def get_llm_instance() -> Optional[OpenAIChat]:
    """Get or create OpenAI LLM instance for summary generation."""
    if OpenAIChat is None:
        return None
    
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return None
    
    try:
        return OpenAIChat(
            model="gpt-4o-mini",  # Fast and cost-effective
            api_key=api_key,
            temperature=0.3,  # Lower temperature for more factual summaries
        )
    except Exception as e:
        print(f"Warning: Failed to initialize LLM: {e}")
        return None


async def generate_patient_summary(
    patient_id: int,
    specialist_type: str = "general",
    query_text: Optional[str] = None,
    custom_prompt: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Generate a patient health summary for a specific specialist.
    
    Args:
        patient_id: Patient/user ID
        specialist_type: Type of specialist (dermatologist, ophthalmologist, etc.)
        query_text: Optional custom query text for RAG retrieval
        custom_prompt: Optional custom prompt for summary generation (overrides specialist_type)
    
    Returns:
        Dictionary with summary, sections, and citations
    """
    from . import pathway_rag_service
    from ..utils.db import get_connection
    
    # Get patient basic info from database
    patient_name = None
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT full_name FROM users WHERE id = %s", (patient_id,))
            row = cur.fetchone()
            if row:
                patient_name = row["full_name"]
    
    # First, get general patient information (age, gender, basic demographics)
    general_query = """
    Extract patient basic information:
    - Patient name
    - Age or date of birth
    - Gender
    - General health overview
    - Chief complaint or reason for visit
    """
    
    general_rag_result = await pathway_rag_service.query_rag(
        query=general_query,
        patient_id=patient_id,
        top_k=5,  # Just a few chunks for basic info
    )
    
    # Get specialist-specific extraction prompt
    specialist_prompt = SPECIALIST_PROMPTS.get(
        specialist_type.lower(), 
        SPECIALIST_PROMPTS["general"]
    )
    
    # Build query based on specialist type or custom prompt
    if query_text:
        query = query_text
    elif custom_prompt:
        # Use custom prompt for specialist-specific extraction
        query = f"""
        Extract all relevant medical information based on this focus:
        {custom_prompt}
        
        Include:
        - Active medications
        - Allergies
        - Recent diagnoses
        - Lab results
        - Imaging findings
        - Current symptoms
        - Relevant medical history
        """
    else:
        query = f"""
        Extract all relevant medical information for a {specialist_type} visit:
        {specialist_prompt}
        
        Include:
        - Active medications
        - Allergies
        - Recent diagnoses
        - Lab results
        - Imaging findings
        - Current symptoms
        - Relevant medical history
        """
    
    # Query Pathway RAG to get relevant information
    rag_result = await pathway_rag_service.query_rag(
        query=query,
        patient_id=patient_id,
        top_k=20,  # Get more chunks for comprehensive summary
    )
    
    if not rag_result.get("retrieved_chunks"):
        return {
            "summary": "No medical records found for this patient.",
            "sections": {},
            "sources": [],
            "specialist_type": specialist_type,
        }
    
    # Combine general patient info
    general_info_text = "\n\n".join([
        f"[Source: {chunk.get('filename', 'Unknown')}]\n{chunk['text']}"
        for chunk in general_rag_result.get("retrieved_chunks", [])
    ])
    
    # Combine retrieved text (clean format for LLM)
    retrieved_text = "\n\n".join([
        f"[Source: {chunk.get('filename', 'Unknown')}]\n{chunk['text']}"
        for chunk in rag_result["retrieved_chunks"]
    ])
    
    # Check if OpenAI API is available
    api_key = os.getenv("OPENAI_API_KEY")
    
    if not api_key or not openai:
        # Fallback: Return retrieved text if LLM not available
        print("⚠️  Warning: OpenAI API not available - returning raw retrieved text")
        return {
            "summary": retrieved_text,
            "sections": _extract_sections_fallback(retrieved_text),
            "sources": rag_result["sources"],
            "specialist_type": specialist_type,
            "note": "LLM not available - showing raw retrieved text",
        }
    
    # Determine the focus for summary (custom prompt or specialist type)
    summary_focus = custom_prompt if custom_prompt else f"{specialist_type} visit"
    
    # Generate summary with LLM - improved prompt
    summary_prompt = f"""You are a medical assistant creating a concise patient health summary for a {summary_focus}.

CRITICAL RULES:
1. Do NOT make diagnoses - only report what is in the source documents
2. Do NOT provide medical recommendations or treatment advice
3. Only include information explicitly stated in the source documents
4. Cite sources using format: [Source: filename] at the end of each fact
5. Keep summary concise and well-organized (1-2 pages maximum)
6. Focus ONLY on information relevant to {specialist_type}
7. Use clear section headers with ## (plain text, NO markdown formatting like **bold**)
8. Use bullet points (•) for lists
9. If information is not available, state "Not documented" rather than guessing
10. DO NOT copy raw text - summarize and organize the information
11. DO NOT use markdown formatting (no **bold**, no __bold__, no *italic*) - use plain text only

Patient Basic Information:
{general_info_text[:2000]}

Patient Medical Records:
{retrieved_text[:6000]}

Create a well-structured patient health summary. Start with a patient overview section, then include specialist-specific information:

## Patient Overview
• Extract and summarize: Patient name, age (or date of birth), gender
• Provide a brief 2-3 sentence general health summary based on the records
• Include chief complaint or reason for visit if available
• Include [Source: filename] citation for each fact

## Active Medications
• List each medication with dosage and indication
• Include [Source: filename] citation

## Allergies
• List all known allergies and reactions
• Include [Source: filename] citation

## Recent Diagnoses
• List recent diagnoses relevant to {summary_focus}
• Include dates if available
• Include [Source: filename] citation

## Lab Results (if relevant to {summary_focus})
• Include recent lab results with dates and values
• Include [Source: filename] citation

## Imaging Findings (if relevant to {summary_focus})
• Include recent imaging findings with dates
• Include [Source: filename] citation

## Current Symptoms
• List current symptoms relevant to {summary_focus}
• Include [Source: filename] citation

## Relevant Medical History
• Include relevant past medical history for {summary_focus}
• Include [Source: filename] citation

IMPORTANT: 
- Start with the Patient Overview section (age, gender, general summary)
- Then provide specialist-specific sections
- Summarize and organize the information. Do NOT copy raw text verbatim
- Create a clean, professional summary
- Use plain text only (no markdown formatting)"""
    
    try:
        # Generate summary using OpenAI API directly
        print(f"🤖 Calling OpenAI API to generate summary for {specialist_type}...")
        client = openai.AsyncOpenAI(api_key=api_key)
        response = await client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system", 
                    "content": "You are a medical assistant creating patient health summaries. Always cite sources using [Source: filename] format. Never make diagnoses. Summarize and organize information clearly."
                },
                {
                    "role": "user", 
                    "content": summary_prompt
                }
            ],
            temperature=0.3,
            max_tokens=2500,  # Increased for better summaries
        )
        
        summary_text = response.choices[0].message.content
        if not summary_text:
            print("⚠️  Warning: OpenAI returned empty response, using retrieved text")
            summary_text = retrieved_text
        else:
            print(f"✅ Successfully generated summary ({len(summary_text)} characters)")
        
    except Exception as e:
        print(f"❌ Error calling OpenAI API: {e}")
        # Fallback to retrieved text
        summary_text = retrieved_text
    
    # Optional: Quality check (if time permits)
    # Verify each statement is supported by sources
    if os.getenv("ENABLE_QUALITY_CHECK", "false").lower() == "true":
        try:
            summary_text = await _quality_check_summary(
                summary_text, 
                rag_result["retrieved_chunks"],
            )
        except Exception as e:
            print(f"Quality check failed: {e}")
    
    # Extract sections from summary
    sections = _parse_summary_sections(summary_text)
    
    return {
        "summary": summary_text,
        "sections": sections,
        "sources": rag_result["sources"],
        "specialist_type": specialist_type,
        "num_sources": len(rag_result["sources"]),
    }


def _parse_summary_sections(summary_text: str) -> Dict[str, str]:
    """
    Parse summary text into structured sections.
    
    Args:
        summary_text: Generated summary text
    
    Returns:
        Dictionary with section names and content
    """
    sections = {}
    current_section = None
    current_content = []
    
    lines = summary_text.split("\n")
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
        
        # Check if line is a section header
        if line.startswith("#") or (line.isupper() and len(line) < 50):
            # Save previous section
            if current_section:
                sections[current_section] = "\n".join(current_content)
            
            # Start new section
            current_section = line.replace("#", "").strip()
            current_content = []
        else:
            if current_section:
                current_content.append(line)
            else:
                # Content before first section
                if "introduction" not in sections:
                    sections["introduction"] = []
                sections.setdefault("introduction", []).append(line)
    
    # Save last section
    if current_section:
        sections[current_section] = "\n".join(current_content)
    
    return sections


def _extract_sections_fallback(text: str) -> Dict[str, str]:
    """Fallback section extraction when LLM is not available."""
    return {
        "raw_text": text,
        "note": "Sections not parsed - LLM not available",
    }


async def _quality_check_summary(
    summary_text: str,
    source_chunks: List[Dict[str, Any]],
    llm: Optional[Any] = None,
) -> str:
    """
    Quality check: Verify each statement in summary is supported by sources.
    This helps catch hallucinations or mismatches.
    
    Args:
        summary_text: Generated summary
        source_chunks: Source document chunks
        llm: LLM instance for verification
    
    Returns:
        Verified summary (or original if verification fails)
    """
    try:
        # Combine source texts
        source_text = "\n\n".join([chunk["text"] for chunk in source_chunks])
        
        quality_check_prompt = f"""
        Review the following patient summary and verify that each statement is supported by the source documents.
        
        If any statement cannot be verified or contradicts the sources, mark it with [VERIFICATION NEEDED].
        If a statement is not in the sources, mark it with [NOT IN SOURCES].
        
        Summary to verify:
        {summary_text}
        
        Source Documents:
        {source_text}
        
        Return the verified summary with any necessary annotations.
        """
        
        # Use OpenAI API directly if available
        api_key = os.getenv("OPENAI_API_KEY")
        if api_key and openai:
            client = openai.AsyncOpenAI(api_key=api_key)
            response = await client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are a medical document verifier. Check that all statements are supported by sources."},
                    {"role": "user", "content": quality_check_prompt}
                ],
                temperature=0.3,
                max_tokens=2000,
            )
            verified_summary = response.choices[0].message.content or summary_text
        elif llm:
            # Fallback to Pathway LLM
            verified_summary = await llm.__wrapped__(quality_check_prompt)
        else:
            verified_summary = summary_text
        
        return verified_summary
    
    except Exception as e:
        print(f"Quality check failed: {e}")
        return summary_text  # Return original if check fails


def get_available_specialists() -> List[str]:
    """Get list of available specialist types."""
    return list(SPECIALIST_PROMPTS.keys())

