from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.dependencies.auth import require_admin
from app.models.user import User
from app.schemas.user import (
    UserCreate,
    UserListResponse,
    UserResponse,
    UserRoleUpdate,
    UserUpdate,
)
from app.services.user_service import UserService


router = APIRouter(
    prefix="/users",
    tags=["User Management"],
)

user_service = UserService()


@router.post(
    "",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_user(
    user_data: UserCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    return user_service.create_user(
        db=db,
        user_data=user_data,
        current_user_id=current_user.id,
    )


@router.get(
    "",
    response_model=UserListResponse,
)
def get_users(
    page: int = Query(
        default=1,
        ge=1,
    ),
    page_size: int = Query(
        default=20,
        ge=1,
        le=100,
    ),
    search: str | None = Query(
        default=None,
        min_length=1,
        max_length=255,
    ),
    role_id: int | None = Query(
        default=None,
        ge=1,
    ),
    is_active: bool | None = Query(
        default=None,
    ),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    return user_service.get_users(
        db=db,
        page=page,
        page_size=page_size,
        search=search,
        role_id=role_id,
        is_active=is_active,
    )


@router.get(
    "/{user_id}",
    response_model=UserResponse,
)
def get_user_by_id(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    return user_service.get_user_by_id(
        db=db,
        user_id=user_id,
    )


@router.put(
    "/{user_id}",
    response_model=UserResponse,
)
def update_user(
    user_id: int,
    user_data: UserUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    return user_service.update_user(
        db=db,
        user_id=user_id,
        user_data=user_data,
        current_user_id=current_user.id,
    )


@router.patch(
    "/{user_id}/role",
    response_model=UserResponse,
)
def change_user_role(
    user_id: int,
    role_data: UserRoleUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    return user_service.change_role(
        db=db,
        user_id=user_id,
        role_data=role_data,
        current_user_id=current_user.id,
    )


@router.patch(
    "/{user_id}/activate",
    response_model=UserResponse,
)
def activate_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    return user_service.activate_user(
        db=db,
        user_id=user_id,
        current_user_id=current_user.id,
    )


@router.patch(
    "/{user_id}/deactivate",
    response_model=UserResponse,
)
def deactivate_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    return user_service.deactivate_user(
        db=db,
        user_id=user_id,
        current_user_id=current_user.id,
    )


@router.delete(
    "/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    user_service.delete_user(
        db=db,
        user_id=user_id,
        current_user_id=current_user.id,
    )

    return None

