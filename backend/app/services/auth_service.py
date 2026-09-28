from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.exceptions import (
    BadRequestException,
    UnauthorizedException,
)
from app.core.security import (
    create_access_token,
    hash_password,
    verify_password,
)
from app.models.role import Role
from app.models.user import User
from app.repositories.user_repository import UserRepository
from app.schemas.auth import UserRegister


class AuthService:
    def __init__(self) -> None:
        self.user_repository = UserRepository()

    def register(
        self,
        db: Session,
        data: UserRegister,
    ) -> User:
        existing_user = self.user_repository.get_by_email(
            db,
            data.email,
        )

        if existing_user:
            raise BadRequestException(
                "Email already registered"
            )

        role = db.scalar(
            select(Role).where(Role.name == "User")
        )

        if role is None:
            raise BadRequestException(
                "Default User role not found"
            )

        user = User(
            first_name=data.first_name,
            last_name=data.last_name,
            email=data.email,
            hashed_password=hash_password(data.password),
            role_id=role.id,
            is_active=True,
        )

        return self.user_repository.create(
            db,
            user,
        )

    def login(
        self,
        db: Session,
        email: str,
        password: str,
    ) -> str:
        user = self.user_repository.get_by_email(
            db,
            email,
        )

        if user is None:
            raise UnauthorizedException(
                "Invalid email or password"
            )

        if not verify_password(
            password,
            user.hashed_password,
        ):
            raise UnauthorizedException(
                "Invalid email or password"
            )

        if not user.is_active:
            raise UnauthorizedException(
                "User account is inactive"
            )

        token = create_access_token(
            subject=str(user.id),
            role=user.role.name,
        )

        return token