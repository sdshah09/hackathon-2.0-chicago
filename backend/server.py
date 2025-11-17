"""FastAPI server exposing HTTP APIs only."""

from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware

from . import auth_service
from .models import AuthResponse, SigninRequest, SignupRequest


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

