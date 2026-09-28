from sqlalchemy import func, select

from sqlalchemy.orm import Session

from app.models.conflict import Conflict


class ConflictRepository:

    def get_by_id(
        self,
        db: Session,
        conflict_id: int,
    ) -> Conflict | None:
        return db.get(
            Conflict,
            conflict_id,
        )

    def get_by_id_for_user(
        self,
        db: Session,
        conflict_id: int,
        user_id: int,
    ) -> Conflict | None:
        return db.scalar(
            select(Conflict).where(
                Conflict.id == conflict_id,
                Conflict.user_id == user_id,
            )
        )

    def get_all_for_user(
        self,
        db: Session,
        user_id: int,
        limit: int = 100,
    ) -> list[Conflict]:
        query = (
            select(Conflict)
            .where(
                Conflict.user_id == user_id,
            )
            .order_by(Conflict.id.desc())
            .limit(limit)
        )

        return list(db.scalars(query).all())

    def get_pending_for_user(
        self,
        db: Session,
        user_id: int,
        limit: int = 100,
    ) -> list[Conflict]:
        query = (
            select(Conflict)
            .where(
                Conflict.user_id == user_id,
                Conflict.resolution_status == "PENDING",
            )
            .order_by(Conflict.id.asc())
            .limit(limit)
        )

        return list(db.scalars(query).all())

    def get_total_count_for_user(
        self,
        db: Session,
        user_id: int,
    ) -> int:
        query = select(
            func.count(Conflict.id)
        ).where(
            Conflict.user_id == user_id,
        )

        return db.scalar(query) or 0

    def get_count_by_status_for_user(
        self,
        db: Session,
        user_id: int,
        resolution_status: str,
    ) -> int:
        query = select(
            func.count(Conflict.id)
        ).where(
            Conflict.user_id == user_id,
            Conflict.resolution_status == resolution_status,
        )

        return db.scalar(query) or 0

    def create(
        self,
        db: Session,
        conflict: Conflict,
    ) -> Conflict:
        db.add(conflict)
        db.flush()
        db.refresh(conflict)
        return conflict

    def update(
        self,
        db: Session,
        conflict: Conflict,
    ) -> Conflict:
        db.flush()
        db.refresh(conflict)
        return conflict