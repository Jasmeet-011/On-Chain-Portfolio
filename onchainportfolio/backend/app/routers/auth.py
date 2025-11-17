# app/routers/auth.py
from fastapi import APIRouter, HTTPException, status

from app.schemas.auth import SignUpRequest, SignInRequest, UserResponse
from app.services.auth_service import (
    create_user,
    authenticate_user,
    get_user_by_email,
)

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/signup", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def signup(payload: SignUpRequest):
    # check if email already exists
    existing = get_user_by_email(payload.email)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email is already registered",
        )

    user = create_user(payload.name, payload.email, payload.password)

    return UserResponse(
        id=str(user["_id"]),
        name=user["name"],
        email=user["email"],
    )


@router.post("/login", response_model=UserResponse)
def login(payload: SignInRequest):
    user = authenticate_user(payload.email, payload.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    return UserResponse(
        id=str(user["_id"]),
        name=user["name"],
        email=user["email"],
    )
