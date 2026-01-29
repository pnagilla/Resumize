import re
from fastapi import APIRouter, HTTPException, Header
from pydantic import BaseModel, field_validator

from services.auth_service import create_user, authenticate_user, validate_token, delete_token

router = APIRouter()


class SignupRequest(BaseModel):
    name: str
    username: str
    email: str
    password: str

    @field_validator("email")
    @classmethod
    def validate_email(cls, v):
        if not re.match(r"^[^\s@]+@[^\s@]+\.[^\s@]+$", v):
            raise ValueError("Invalid email format")
        return v.lower()


class LoginRequest(BaseModel):
    email: str
    password: str


class AuthResponse(BaseModel):
    user: dict
    token: str


@router.post("/auth/signup", response_model=AuthResponse)
async def signup(request: SignupRequest):
    """Register a new user."""
    if len(request.password) < 8:
        raise HTTPException(status_code=400, detail="Password must be at least 8 characters")

    if not re.search(r"[A-Za-z]", request.password) or not re.search(r"\d", request.password):
        raise HTTPException(status_code=400, detail="Password must contain both letters and numbers")

    if len(request.name.strip()) < 2:
        raise HTTPException(status_code=400, detail="Name must be at least 2 characters")

    if len(request.username.strip()) < 3:
        raise HTTPException(status_code=400, detail="Username must be at least 3 characters")

    if not re.match(r"^[a-zA-Z0-9_]+$", request.username.strip()):
        raise HTTPException(status_code=400, detail="Username can only contain letters, numbers, and underscores")

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
async def logout(authorization: str = Header(default="")):
    """Logout and invalidate the current token."""
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing authorization token")

    token = authorization[7:]
    deleted = delete_token(token)

    if not deleted:
        raise HTTPException(status_code=400, detail="Invalid token")

    return {"message": "Logged out successfully"}


@router.get("/auth/me")
async def get_current_user(authorization: str = Header(default="")):
    """Get current user from token."""
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing authorization token")

    token = authorization[7:]
    user = validate_token(token)

    if not user:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    return {"user": user}


class ForgotPasswordRequest(BaseModel):
    email: str


@router.post("/auth/forgot-password")
async def forgot_password(request: ForgotPasswordRequest):
    """Send password reset email (placeholder)."""
    return {"message": "If an account exists with this email, a reset link will be sent."}
