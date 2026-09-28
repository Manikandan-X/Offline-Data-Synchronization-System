from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.db.session import get_db

from app.schemas.auth import (
    PasswordChange,
    TokenResponse,
    UserLogin,
    UserRegister,
)

from app.schemas.user import UserResponse, UserUpdate

from app.services.auth_service import AuthService
from app.services.user_service import UserService
from app.dependencies.auth import get_current_user
from app.models.user import User


router = APIRouter(
    prefix="/auth",
    tags=["Authentication"],
)

auth_service = AuthService()
user_service = UserService()


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
)
def register(
    data: UserRegister,
    db: Session = Depends(get_db),
):
    user = auth_service.register(
        db=db,
        data=data,
    )

    db.commit()
    db.refresh(user)

    return user


@router.post(
    "/login",
    response_model=TokenResponse,
)
def login(
    data: UserLogin,
    db: Session = Depends(get_db),
):
    access_token = auth_service.login(
        db=db,
        email=data.email,
        password=data.password,
    )

    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
    )


@router.get(
    "/me",
    response_model=UserResponse,
)
def get_current_user_details(
    current_user: User = Depends(get_current_user),
):
    return current_user


@router.put(
    "/me",
    response_model=UserResponse,
)
def update_current_user_profile(
    profile_data: UserUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Self-service profile update. Any logged-in user (Admin or User) can
    change their own first name, last name, and email here. There is no
    role_id field on this schema, so a user can never grant themselves a
    different role through this endpoint — role changes remain admin-only
    via PUT /users/{user_id}/role.
    """

    return user_service.update_user(
        db=db,
        user_id=current_user.id,
        user_data=profile_data,
        current_user_id=current_user.id,
    )


@router.put(
    "/me/password",
    response_model=UserResponse,
)
def change_current_user_password(
    password_data: PasswordChange,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Self-service password change. Requires the caller's current password
    for verification. No OTP / email confirmation step, as requested.
    """

    return user_service.change_own_password(
        db=db,
        current_user=current_user,
        password_data=password_data,
    )