from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.role import Role
from app.models.user import User


class UserRepository:

    def get_by_email(
        self,
        db: Session,
        email: str,
    ) -> User | None:
        return db.scalar(
            select(User).where(User.email == email)
        )

    def get_by_id(
        self,
        db: Session,
        user_id: int,
    ) -> User | None:
        return db.get(User, user_id)

    def get_all(
        self,
        db: Session,
        page: int,
        page_size: int,
        search: str | None = None,
        role_id: int | None = None,
        is_active: bool | None = None,
    ) -> tuple[list[User], int]:

        query = select(User)
        count_query = select(func.count(User.id))

        if search:
            search_pattern = f"%{search}%"

            search_condition = (
                (User.first_name.ilike(search_pattern))
                | (User.last_name.ilike(search_pattern))
                | (User.email.ilike(search_pattern))
            )

            query = query.where(search_condition)
            count_query = count_query.where(search_condition)

        if role_id is not None:
            query = query.where(User.role_id == role_id)
            count_query = count_query.where(User.role_id == role_id)

        if is_active is not None:
            query = query.where(User.is_active == is_active)
            count_query = count_query.where(User.is_active == is_active)

        query = (
            query
            .order_by(User.id.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )

        users = list(
            db.scalars(query).all()
        )

        total = db.scalar(count_query) or 0

        return users, total

    def get_role_by_id(
        self,
        db: Session,
        role_id: int,
    ) -> Role | None:
        return db.get(Role, role_id)

    def create(
        self,
        db: Session,
        user: User,
    ) -> User:
        db.add(user)
        db.flush()
        db.refresh(user)

        return user

    def update(
        self,
        db: Session,
        user: User,
    ) -> User:
        db.flush()
        db.refresh(user)

        return user

    def delete(
        self,
        db: Session,
        user: User,
    ) -> None:
        db.delete(user)
        db.flush()

    def set_active_status(
        self,
        db: Session,
        user: User,
        is_active: bool,
    ) -> User:
        user.is_active = is_active

        db.flush()
        db.refresh(user)

        return user