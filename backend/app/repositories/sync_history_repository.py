from datetime import datetime

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.sync_history import SyncHistory


class SyncHistoryRepository:

    def get_by_id(
        self,
        db: Session,
        history_id: int,
    ) -> SyncHistory | None:
        return db.get(
            SyncHistory,
            history_id,
        )

    def get_all_for_user(
        self,
        db: Session,
        user_id: int,
        limit: int = 100,
    ) -> list[SyncHistory]:
        query = (
            select(SyncHistory)
            .where(
                SyncHistory.user_id == user_id,
            )
            .order_by(SyncHistory.id.desc())
            .limit(limit)
        )

        return list(db.scalars(query).all())

    def get_last_sync_time_for_user(
        self,
        db: Session,
        user_id: int,
    ) -> datetime | None:
        query = select(
            func.max(SyncHistory.created_at)
        ).where(
            SyncHistory.user_id == user_id,
        )

        return db.scalar(query)

    def create(
        self,
        db: Session,
        history: SyncHistory,
    ) -> SyncHistory:
        db.add(history)
        db.flush()
        db.refresh(history)

        return history