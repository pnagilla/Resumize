from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from services.auth_service import create_user, authenticate_user, validate_token, delete_token

router = APIRouter()


class SignupRequest(BaseModel):
    name: str
    username: str
    email: str
    password: str


class LoginRequest(BaseModel):
    email: str
    password: str


class AuthResponse(BaseModel):
    user: dict
    token: str


@router.post("/auth/signup", response_model=AuthResponse)
async def signup(request: SignupRequest):
    """Register a new user."""
    if len(request.password) < 6:
        raise HTTPException(status_code=400, detail="Password must be at least 6 characters")

    if len(request.name.strip()) < 2:
        raise HTTPException(status_code=400, detail="Name must be at least 2 characters")

    if len(request.username.strip()) < 3:
        raise HTTPException(status_code=400, detail="Username must be at least 3 characters")

    result = create_user(
        name=request.name.strip(),
        username=request.username.strip(),
        email=request.email,
        password=request.password
    )

    if not result:
        raise HTTPException(status_code=400, detail="Email or username already registered")

    return result


@router.post("/auth/login", response_model=AuthResponse)
async def login(request: LoginRequest):
    """Login with email and password."""
    result = authenticate_user(
        email=request.email,
        password=request.password
    )

    if not result:
        raise HTTPException(status_code=401, detail="Invalid email or password")

    return result


@router.post("/auth/logout")
async def logout(token: str):
    """Logout and invalidate token."""
    deleted = delete_token(token)

    if not deleted:
        raise HTTPException(status_code=400, detail="Invalid token")

    return {"message": "Logged out successfully"}


@router.get("/auth/me")
async def get_current_user(token: str):
    """Get current user from token."""
    user = validate_token(token)

    if not user:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    return {"user": user}


class ForgotPasswordRequest(BaseModel):
    email: str


@router.post("/auth/forgot-password")
async def forgot_password(request: ForgotPasswordRequest):
    """Send password reset email (placeholder)."""
    # In production, this would send an email with a reset link
    # For now, just return success
    return {"message": "If an account exists with this email, a reset link will be sent."}
