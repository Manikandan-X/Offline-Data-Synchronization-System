import math

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.exceptions import BadRequestException, NotFoundException
from app.core.security import hash_password, verify_password
from app.models.user import User
from app.repositories.user_repository import UserRepository
from app.schemas.user import UserCreate, UserRoleUpdate, UserUpdate
from app.schemas.auth import PasswordChange

from app.constants.audit import AuditAction, AuditEntity
from app.services.audit_log_service import AuditLogService


class UserService:

    def __init__(self):
        self.user_repository = UserRepository()
        self.audit_log_service = AuditLogService()

    # ---------------------------------------------------------
    # CREATE USER
    # ---------------------------------------------------------
    def create_user(
        self,
        db: Session,
        user_data: UserCreate,
        current_user_id: int,
    ) -> User:

        existing_user = self.user_repository.get_by_email(
            db=db,
            email=user_data.email,
        )

        if existing_user is not None:
            raise BadRequestException(
                "Email already registered"
            )

        role = self.user_repository.get_role_by_id(
            db=db,
            role_id=user_data.role_id,
        )

        if role is None:
            raise NotFoundException(
                "Role not found"
            )

        user = User(
            first_name=user_data.first_name,
            last_name=user_data.last_name,
            email=user_data.email,
            hashed_password=hash_password(
                user_data.password
            ),
            role_id=user_data.role_id,
            is_active=True,
        )

        try:
            user = self.user_repository.create(
                db=db,
                user=user,
            )
            
            self.audit_log_service.create_log(
                db=db,
                user_id=current_user_id,
                action=AuditAction.USER_CREATED,
                entity_type=AuditEntity.USER,
                entity_id=user.id,
                details={
                    "email": user.email,
                    "role_id": user.role_id,
                },
            )

            db.commit()
            db.refresh(user)

            return user

        except IntegrityError:
            db.rollback()

            raise BadRequestException(
                "Unable to create user"
            )

    # ---------------------------------------------------------
    # GET USERS
    # ---------------------------------------------------------
    def get_users(
        self,
        db: Session,
        page: int,
        page_size: int,
        search: str | None = None,
        role_id: int | None = None,
        is_active: bool | None = None,
    ) -> dict:

        users, total = self.user_repository.get_all(
            db=db,
            page=page,
            page_size=page_size,
            search=search,
            role_id=role_id,
            is_active=is_active,
        )

        total_pages = (
            math.ceil(total / page_size)
            if total > 0
            else 0
        )

        return {
            "items": users,
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": total_pages,
        }

    # ---------------------------------------------------------
    # GET USER BY ID
    # ---------------------------------------------------------
    def get_user_by_id(
        self,
        db: Session,
        user_id: int,
    ) -> User:

        user = self.user_repository.get_by_id(
            db=db,
            user_id=user_id,
        )

        if user is None:
            raise NotFoundException(
                "User not found"
            )

        return user

    # ---------------------------------------------------------
    # UPDATE USER
    # ---------------------------------------------------------
    def update_user(
        self,
        db: Session,
        user_id: int,
        user_data: UserUpdate,
        current_user_id: int,
    ) -> User:

        user = self.get_user_by_id(
            db=db,
            user_id=user_id,
        )

        if user_data.email is not None:

            existing_user = self.user_repository.get_by_email(
                db=db,
                email=user_data.email,
            )

            if (
                existing_user is not None
                and existing_user.id != user.id
            ):
                raise BadRequestException(
                    "Email already registered"
                )

            user.email = user_data.email

        if user_data.first_name is not None:
            user.first_name = user_data.first_name

        if user_data.last_name is not None:
            user.last_name = user_data.last_name

        try:
            user = self.user_repository.update(
                db=db,
                user=user,
            )
            
            self.audit_log_service.create_log(
                db=db,
                user_id=current_user_id,
                action=AuditAction.USER_UPDATED,
                entity_type=AuditEntity.USER,
                entity_id=user.id,
                details={
                    "email": user.email,
                    "first_name": user.first_name,
                    "last_name": user.last_name,
                },
            )

            db.commit()
            db.refresh(user)

            return user

        except IntegrityError:
            db.rollback()

            raise BadRequestException(
                "Unable to update user"
            )

    # ---------------------------------------------------------
    # CHANGE ROLE
    # ---------------------------------------------------------
    def change_role(
        self,
        db: Session,
        user_id: int,
        role_data: UserRoleUpdate,
        current_user_id: int,
    ) -> User:

        user = self.get_user_by_id(
            db=db,
            user_id=user_id,
        )

        role = self.user_repository.get_role_by_id(
            db=db,
            role_id=role_data.role_id,
        )

        if role is None:
            raise NotFoundException(
                "Role not found"
            )

        user.role_id = role.id

        try:
            user = self.user_repository.update(
                db=db,
                user=user,
            )
            
            self.audit_log_service.create_log(
                db=db,
                user_id=current_user_id,
                action=AuditAction.USER_ROLE_CHANGED,
                entity_type=AuditEntity.USER,
                entity_id=user.id,
                details={
                    "new_role_id": role.id,
                },
            )

            db.commit()
            db.refresh(user)

            return user

        except IntegrityError:
            db.rollback()

            raise BadRequestException(
                "Unable to change user role"
            )

    # ---------------------------------------------------------
    # ACTIVATE USER
    # ---------------------------------------------------------
    def activate_user(
        self,
        db: Session,
        user_id: int,
        current_user_id: int,
    ) -> User:

        user = self.get_user_by_id(
            db=db,
            user_id=user_id,
        )

        if user.id == current_user_id:
            raise BadRequestException(
                "You cannot change your own account status"
            )

        if user.is_active:
            raise BadRequestException(
                "User is already active"
            )

        user = self.user_repository.set_active_status(
            db=db,
            user=user,
            is_active=True,
        )
        self.audit_log_service.create_log(
            db=db,
            user_id=current_user_id,
            action=AuditAction.USER_ACTIVATED,
            entity_type=AuditEntity.USER,
            entity_id=user.id,
        )

        db.commit()
        db.refresh(user)

        return user

    # ---------------------------------------------------------
    # DEACTIVATE USER
    # ---------------------------------------------------------
    def deactivate_user(
        self,
        db: Session,
        user_id: int,
        current_user_id: int,
    ) -> User:

        user = self.get_user_by_id(
            db=db,
            user_id=user_id,
        )

        if user.id == current_user_id:
            raise BadRequestException(
                "You cannot change your own account status"
            )

        if not user.is_active:
            raise BadRequestException(
                "User is already inactive"
            )

        user = self.user_repository.set_active_status(
            db=db,
            user=user,
            is_active=False,
        )
        
        self.audit_log_service.create_log(
            db=db,
            user_id=current_user_id,
            action=AuditAction.USER_DEACTIVATED,
            entity_type=AuditEntity.USER,
            entity_id=user.id,
        )

        db.commit()
        db.refresh(user)

        return user

    # ---------------------------------------------------------
    # DELETE USER
    # ---------------------------------------------------------
    def delete_user(
        self,
        db: Session,
        user_id: int,
        current_user_id: int,
    ) -> None:

        user = self.get_user_by_id(
            db=db,
            user_id=user_id,
        )

        if user.id == current_user_id:
            raise BadRequestException(
                "You cannot delete your own account"
            )

        try:
            self.user_repository.delete(
                db=db,
                user=user,
            )
            
            self.audit_log_service.create_log(
                db=db,
                user_id=current_user_id,
                action=AuditAction.USER_DELETED,
                entity_type=AuditEntity.USER,
                entity_id=user.id,
                details={
                    "email": user.email,
                },
            )

            db.commit()

        except IntegrityError:
            db.rollback()

            raise BadRequestException(
                "Unable to delete user because the user is associated with other data"
            )

    # ---------------------------------------------------------
    # CHANGE OWN PASSWORD (self-service)
    # ---------------------------------------------------------
    def change_own_password(
        self,
        db: Session,
        current_user: User,
        password_data: PasswordChange,
    ) -> User:

        if not verify_password(
            password_data.current_password,
            current_user.hashed_password,
        ):
            raise BadRequestException(
                "Current password is incorrect"
            )

        current_user.hashed_password = hash_password(
            password_data.new_password
        )

        try:
            user = self.user_repository.update(
                db=db,
                user=current_user,
            )

            self.audit_log_service.create_log(
                db=db,
                user_id=current_user.id,
                action=AuditAction.USER_PASSWORD_CHANGED,
                entity_type=AuditEntity.USER,
                entity_id=current_user.id,
            )

            db.commit()
            db.refresh(user)

            return user

        except IntegrityError:
            db.rollback()

            raise BadRequestException(
                "Unable to change password"
            )
