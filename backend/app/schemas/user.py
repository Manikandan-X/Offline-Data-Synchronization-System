from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class UserCreate(BaseModel):
    first_name: str = Field(
        ...,
        min_length=1,
        max_length=100,
    )
    last_name: str = Field(
        ...,
        min_length=1,
        max_length=100,
    )
    email: EmailStr
    password: str = Field(
        ...,
        min_length=8,
        max_length=128,
    )
    role_id: int = Field(
        ...,
        gt=0,
    )


class UserUpdate(BaseModel):
    first_name: str | None = Field(
        default=None,
        min_length=1,
        max_length=100,
    )
    last_name: str | None = Field(
        default=None,
        min_length=1,
        max_length=100,
    )
    email: EmailStr | None = None


class UserRoleUpdate(BaseModel):
    role_id: int = Field(
        ...,
        gt=0,
    )


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    first_name: str
    last_name: str
    email: EmailStr
    is_active: bool
    role_id: int
    created_at: datetime
    updated_at: datetime


class UserListResponse(BaseModel):
    items: list[UserResponse]
    total: int
    page: int
    page_size: int
    total_pages: int