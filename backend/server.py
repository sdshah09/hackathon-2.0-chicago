"""FastAPI server exposing HTTP APIs only."""

from typing import List

from fastapi import BackgroundTasks, Depends, FastAPI, File, HTTPException, UploadFile, status
from fastapi.middleware.cors import CORSMiddleware

from . import auth_service
from .models import AuthResponse, FileRecord, FileUploadResponse, SigninRequest, SignupRequest
from .services import file_service


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
    background_tasks: BackgroundTasks = BackgroundTasks(),
) -> FileUploadResponse:
    """
    Upload multiple files (JPEG, PNG, PDF) for a user.
    Files are uploaded to S3 asynchronously in the background.
    Returns immediately with file metadata.
    """
    # Get user_id from username
    patient_id = get_user_id_from_username(username)
    # Allowed file types
    allowed_types = {"image/jpeg", "image/jpg", "image/png", "application/pdf"}
    max_file_size = 50 * 1024 * 1024  # 50MB limit

    file_records = []

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

    return FileUploadResponse(
        message=f"Successfully queued {len(file_records)} file(s) for upload",
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

