from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import select
from sqlalchemy.orm import Session

try:
    from app.core.security import (
        create_access_token,
        hash_password,
        verify_password,
    )
    from app.database import get_db
    from app.models.user import User
    from app.schemas.auth import (
        TokenResponse,
        UserLogin,
        UserRegister,
        UserResponse,
    )
except ModuleNotFoundError:
    from backend.app.core.security import (
        create_access_token,
        hash_password,
        verify_password,
    )
    from backend.app.database import get_db
    from backend.app.models.user import User
    from backend.app.schemas.auth import (
        TokenResponse,
        UserLogin,
        UserRegister,
        UserResponse,
    )


router = APIRouter(
    prefix="/auth",
    tags=["Authentication"],
)


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
)
def register_user(
    payload: UserRegister,
    db: Session = Depends(get_db),
):
    existing_user = db.scalar(
        select(User).where(User.email == payload.email)
    )

    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A user with this email already exists.",
        )

    user = User(
        full_name=payload.full_name,
        email=payload.email,
        password_hash=hash_password(payload.password),
        role="student",
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    return user


@router.post(
    "/login",
    response_model=TokenResponse,
)
def login_user(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
):
    user = db.scalar(
        select(User).where(User.email == form_data.username)
    )

    if not user or not verify_password(
        form_data.password,
        user.password_hash,
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password.",
            headers={
                "WWW-Authenticate": "Bearer",
            },
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This account is inactive.",
        )

    token = create_access_token(
        subject=str(user.id),
    )

    return {
        "access_token": token,
        "token_type": "bearer",
    }