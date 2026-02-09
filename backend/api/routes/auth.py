"""
Auth route handlers - Registration, Login, Profile.
"""

from fastapi import APIRouter, Depends
from pydantic import BaseModel, EmailStr
from typing import Optional

from backend.auth import register_user, login_user, get_current_user

router = APIRouter(prefix="/auth", tags=["authentication"])


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    full_name: str
    role: Optional[str] = "developer"


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class AuthResponse(BaseModel):
    token: str
    user: dict


@router.post("/register", response_model=AuthResponse)
async def register(request: RegisterRequest):
    """Register a new user account."""
    return register_user(
        email=request.email,
        password=request.password,
        full_name=request.full_name,
        role=request.role or "developer",
    )


@router.post("/login", response_model=AuthResponse)
async def login(request: LoginRequest):
    """Login with email and password."""
    return login_user(email=request.email, password=request.password)


@router.get("/me")
async def get_profile(user=Depends(get_current_user)):
    """Get current user profile."""
    return user
