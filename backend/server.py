"""FastAPI server exposing HTTP APIs only."""

from typing import List, Optional

from fastapi import BackgroundTasks, Depends, FastAPI, File, Form, HTTPException, UploadFile, status
from fastapi.middleware.cors import CORSMiddleware

from . import auth_service
from .models import (
    AuthResponse,
    FileRecord,
    FileUploadResponse,
    RAGQueryRequest,
    RAGQueryResponse,
    SigninRequest,
    SignupRequest,
    SummaryRequest,
    SummaryResponse,
    SummaryPdfResponse,
)
from .services import file_service, pathway_rag_service, summary_service, orchestration_service


app = FastAPI(title="Patient Summary Backend", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.post("/auth/signup", response_model=AuthResponse, tags=["auth"])
async def signup(payload: SignupRequest) -> AuthResponse:
    try:
        user = auth_service.register_user(
            username=payload.username,
            password=payload.password,
            full_name=payload.full_name,
        )
        return AuthResponse(message="User created successfully", user=user)
    except auth_service.UserAlreadyExistsError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc
    except auth_service.AuthenticationError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc),
        ) from exc


@app.post("/auth/signin", response_model=AuthResponse, tags=["auth"])
async def signin(payload: SigninRequest) -> AuthResponse:
    try:
        user = auth_service.authenticate_user(
            username=payload.username, password=payload.password
        )
        return AuthResponse(message="Login successful", user=user)
    except auth_service.InvalidCredentialsError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(exc),
        ) from exc


@app.get("/health", tags=["system"])
async def healthcheck() -> dict[str, str]:
    return {"status": "ok"}


def get_user_id_from_username(username: str) -> int:
    """
    Get user ID from username and verify user exists.
    Returns user_id if found, raises 404 if not found.
    """
    from .utils.db import get_connection

    # Normalize username (lowercase, trimmed)
    normalized_username = username.strip().lower()

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT id FROM users WHERE username = %s", (normalized_username,))
            row = cur.fetchone()
            if not row:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"User with username '{username}' not found",
                )
            return row["id"]


@app.post(
    "/users/{username}/files/upload",
    response_model=FileUploadResponse,
    tags=["files"],
)
async def upload_files(
    username: str,
    files: List[UploadFile] = File(...),
    specialist_type: str = Form(default="general"),
    custom_prompt: Optional[str] = Form(default=None),
    background_tasks: BackgroundTasks = BackgroundTasks(),
) -> FileUploadResponse:
    """
    Upload multiple files (JPEG, PNG, PDF) for a user with specialist type.
    Files are uploaded to S3 asynchronously, then processed through Pathway,
    and a summary PDF is generated and uploaded to S3.
    Returns immediately with file metadata.
    
    Args:
        username: Username of the patient
        files: List of files to upload
        specialist_type: Type of specialist (dermatologist, ophthalmologist, etc.)
        custom_prompt: Optional custom prompt for summary generation (overrides specialist_type focus)
    """
    # Get user_id from username
    patient_id = get_user_id_from_username(username)
    
    # Validate specialist type (only if custom_prompt is not provided)
    if not custom_prompt:
        from .services.summary_service import get_available_specialists
        available_specialists = get_available_specialists()
        if specialist_type.lower() not in available_specialists:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid specialist_type: {specialist_type}. Available: {', '.join(available_specialists)}",
            )
    
    # Allowed file types
    allowed_types = {"image/jpeg", "image/jpg", "image/png", "application/pdf"}
    max_file_size = 50 * 1024 * 1024  # 50MB limit

    file_records = []
    file_ids = []

    for file in files:
        # Validate file type
        if not file.content_type or file.content_type.lower() not in allowed_types:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid file type: {file.content_type}. Allowed: JPEG, PNG, PDF",
            )

        # Read file content (needed for size check and upload)
        file_content = await file.read()
        file_size = len(file_content)

        # Validate file size
        if file_size > max_file_size:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"File {file.filename} exceeds maximum size of 50MB",
            )

        # Normalize file type
        file_type = file_service._normalize_file_type(file.content_type)
        content_type = file.content_type or "application/octet-stream"
        filename = file.filename or "unknown"

        # Create file record in database immediately
        file_record = file_service.create_file_record(
            patient_id=patient_id,
            filename=filename,
            file_type=file_type,
            file_size=file_size,
        )

        # Queue async S3 upload (pass file content as bytes, not file object)
        background_tasks.add_task(
            file_service.upload_file_to_s3_async,
            file_content=file_content,
            filename=filename,
            content_type=content_type,
            file_id=file_record["id"],
            patient_id=patient_id,
        )

        file_records.append(
            FileRecord(
                id=file_record["id"],
                patient_id=patient_id,
                filename=file_record["filename"],
                file_type=file_record["file_type"],
                file_size=file_record["file_size"],
                upload_status=file_record["upload_status"],
                extraction_status="pending",
                created_at=file_record["created_at"],
            )
        )
        file_ids.append(file_record["id"])

    # Create summary PDF record and trigger end-to-end processing
    summary_record = orchestration_service.create_summary_pdf_record(
        patient_id=patient_id,
        specialist_type=specialist_type.lower(),
        file_ids=file_ids,
    )
    summary_id = summary_record["id"]
    
    # Trigger end-to-end pipeline in background
    background_tasks.add_task(
        orchestration_service.process_end_to_end_pipeline,
        patient_id=patient_id,
        file_ids=file_ids,
        specialist_type=specialist_type.lower(),
        summary_id=summary_id,
        custom_prompt=custom_prompt,
    )

    return FileUploadResponse(
        message=f"Successfully queued {len(file_records)} file(s) for upload. Summary PDF processing started (ID: {summary_id})",
        files=file_records,
    )


@app.get("/users/{username}/files", tags=["files"])
async def get_user_files(
    username: str,
) -> List[FileRecord]:
    """Get all files for a user."""
    # Get user_id from username
    patient_id = get_user_id_from_username(username)
    files = file_service.get_patient_files(patient_id)
    return [
        FileRecord(
            id=f["id"],
            patient_id=patient_id,
            filename=f["filename"],
            file_type=f["file_type"],
            file_size=f["file_size"],
            s3_url=f.get("s3_url"),
            upload_status=f["upload_status"],
            extraction_status=f["extraction_status"],
            created_at=f["created_at"],
        )
        for f in files
    ]


@app.post(
    "/users/{username}/query",
    response_model=RAGQueryResponse,
    tags=["rag"],
)
async def query_patient_records(
    username: str,
    request: RAGQueryRequest,
) -> RAGQueryResponse:
    """
    Query patient records using RAG.
    Searches through all indexed documents for the patient and returns relevant information.
    """
    # Get user_id from username
    patient_id = get_user_id_from_username(username)
    
    # Query RAG pipeline
    result = await pathway_rag_service.query_rag(
        query=request.query,
        patient_id=patient_id,
        top_k=request.top_k,
    )
    
    # Convert sources to response model
    from .models import Source
    sources = [
        Source(
            filename=s["filename"],
            file_id=s["file_id"],
            s3_url=s.get("s3_url"),
            chunk_index=s["chunk_index"],
        )
        for s in result["sources"]
    ]
    
    return RAGQueryResponse(
        query=result["query"],
        answer=result["answer"],
        sources=sources,
        num_chunks_found=result["num_chunks_found"],
    )


@app.get("/users/{username}/documents", tags=["rag"])
async def get_patient_documents(
    username: str,
) -> dict:
    """
    Get all indexed documents for a patient.
    Returns summary of documents stored in Pathway index.
    """
    # Get user_id from username
    patient_id = get_user_id_from_username(username)
    
    documents = pathway_rag_service.get_patient_documents(patient_id)
    
    return {
        "patient_id": patient_id,
        "username": username,
        "documents": documents,
        "total_documents": len(documents),
    }


@app.post(
    "/users/{username}/summary",
    response_model=SummaryResponse,
    tags=["summary"],
)
async def generate_patient_summary(
    username: str,
    request: SummaryRequest,
) -> SummaryResponse:
    """
    Generate a patient health summary for a specific specialist.
    
    Creates a 1-2 page summary with:
    - Patient Overview (name, age, gender, general summary)
    - Active medications
    - Allergies
    - Recent diagnoses
    - Lab results
    - Imaging findings
    - Current symptoms
    - Relevant medical history
    
    Parameters:
    - specialist_type: Type of specialist (dermatologist, ophthalmologist, etc.)
    - custom_query: Optional custom query for RAG retrieval
    - custom_prompt: Optional custom prompt for summary generation (overrides specialist_type focus)
    
    All information is traceable to source documents with citations.
    """
    # Get user_id from username
    patient_id = get_user_id_from_username(username)
    
    # Generate summary
    result = await summary_service.generate_patient_summary(
        patient_id=patient_id,
        specialist_type=request.specialist_type,
        query_text=request.custom_query,
        custom_prompt=request.custom_prompt,
    )
    
    # Convert sources to response model
    from .models import Source
    sources = [
        Source(
            filename=s["filename"],
            file_id=s["file_id"],
            s3_url=s.get("s3_url"),
            chunk_index=s["chunk_index"],
        )
        for s in result["sources"]
    ]
    
    return SummaryResponse(
        summary=result["summary"],
        sections=result["sections"],
        sources=sources,
        specialist_type=result["specialist_type"],
        num_sources=result.get("num_sources", len(sources)),
        note=result.get("note"),
    )


@app.get("/specialists", tags=["summary"])
async def get_available_specialists() -> dict:
    """Get list of available specialist types for summary generation."""
    specialists = summary_service.get_available_specialists()
    return {
        "specialists": specialists,
        "description": "Available specialist types for generating tailored patient summaries",
    }


@app.get(
    "/users/{username}/summary-pdf",
    response_model=SummaryPdfResponse,
    tags=["summary"],
)
async def get_summary_pdf(
    username: str,
    specialist_type: str = "general",
) -> SummaryPdfResponse:
    """
    Get the latest summary PDF for a user and specialist type.
    Returns the S3 download link when processing is complete.
    """
    # Get user_id from username
    patient_id = get_user_id_from_username(username)
    
    # Get latest summary PDF
    summary_pdf = orchestration_service.get_latest_summary_pdf(
        patient_id=patient_id,
        specialist_type=specialist_type.lower(),
    )
    
    if not summary_pdf:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No summary PDF found for specialist type: {specialist_type}",
        )
    
    if summary_pdf["status"] == "processing":
        return SummaryPdfResponse(
            summary_id=summary_pdf["id"],
            status="processing",
            s3_url=None,
            specialist_type=summary_pdf["specialist_type"],
            message="Summary PDF is being generated. Please check again in a few moments.",
            created_at=summary_pdf["created_at"],
        )
    elif summary_pdf["status"] == "failed":
        return SummaryPdfResponse(
            summary_id=summary_pdf["id"],
            status="failed",
            s3_url=None,
            specialist_type=summary_pdf["specialist_type"],
            message="Summary PDF generation failed. Please try uploading files again.",
            created_at=summary_pdf["created_at"],
        )
    else:
        return SummaryPdfResponse(
            summary_id=summary_pdf["id"],
            status="completed",
            s3_url=summary_pdf["s3_url"],
            specialist_type=summary_pdf["specialist_type"],
            message="Summary PDF is ready for download.",
            created_at=summary_pdf["created_at"],
        )

