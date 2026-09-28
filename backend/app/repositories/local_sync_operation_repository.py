from datetime import datetime

from sqlalchemy import and_, func, select
from sqlalchemy.orm import Session

from app.models.local_sync_operation import LocalSyncOperation


class LocalSyncOperationRepository:

    def get_by_id(
        self,
        db: Session,
        operation_db_id: int,
    ) -> LocalSyncOperation | None:
        return db.get(
            LocalSyncOperation,
            operation_db_id,
        )

    def get_by_operation_id(
        self,
        db: Session,
        operation_id: str,
    ) -> LocalSyncOperation | None:
        return db.scalar(
            select(LocalSyncOperation).where(
                LocalSyncOperation.operation_id == operation_id,
            )
        )

    def get_by_operation_id_for_user(
        self,
        db: Session,
        operation_id: str,
        user_id: int,
    ) -> LocalSyncOperation | None:
        return db.scalar(
            select(LocalSyncOperation).where(
                LocalSyncOperation.operation_id == operation_id,
                LocalSyncOperation.user_id == user_id,
            )
        )

    def get_pending_for_user(
        self,
        db: Session,
        user_id: int,
        limit: int = 100,
    ) -> list[LocalSyncOperation]:
        query = (
            select(LocalSyncOperation)
            .where(
                LocalSyncOperation.user_id == user_id,
                LocalSyncOperation.status == "PENDING",
            )
            .order_by(LocalSyncOperation.id.asc())
            .limit(limit)
        )

        return list(db.scalars(query).all())

    def get_total_count_for_user(
        self,
        db: Session,
        user_id: int,
    ) -> int:
        query = select(
            func.count(LocalSyncOperation.id)
        ).where(
            LocalSyncOperation.user_id == user_id,
        )

        return db.scalar(query) or 0

    def get_count_by_status_for_user(
        self,
        db: Session,
        user_id: int,
        status: str,
    ) -> int:
        query = select(
            func.count(LocalSyncOperation.id)
        ).where(
            LocalSyncOperation.user_id == user_id,
            LocalSyncOperation.status == status,
        )

        return db.scalar(query) or 0

    def search_for_user(
        self,
        db: Session,
        user_id: int,
        operation_id: str | None = None,
        status: str | None = None,
        operation_type: str | None = None,
        from_date: datetime | None = None,
        to_date: datetime | None = None,
        page: int = 1,
        page_size: int = 10,
        sort_by: str = "created_at",
        sort_order: str = "desc",
    ) -> tuple[list[LocalSyncOperation], int]:

        conditions = [
            LocalSyncOperation.user_id == user_id,
        ]

        if operation_id is not None:
            conditions.append(
                LocalSyncOperation.operation_id == operation_id
            )

        if status is not None:
            conditions.append(
                LocalSyncOperation.status == status
            )

        if operation_type is not None:
            conditions.append(
                LocalSyncOperation.operation_type == operation_type
            )

        if from_date is not None:
            conditions.append(
                LocalSyncOperation.created_at >= from_date
            )

        if to_date is not None:
            conditions.append(
                LocalSyncOperation.created_at <= to_date
            )

        count_query = select(
            func.count(LocalSyncOperation.id)
        ).where(
            and_(*conditions)
        )

        total = db.scalar(count_query) or 0

        sort_columns = {
            "id": LocalSyncOperation.id,
            "operation_id": LocalSyncOperation.operation_id,
            "operation_type": LocalSyncOperation.operation_type,
            "status": LocalSyncOperation.status,
            "created_at": LocalSyncOperation.created_at,
            "updated_at": LocalSyncOperation.updated_at,
        }

        sort_column = sort_columns.get(sort_by)

        if sort_column is None:
            sort_column = LocalSyncOperation.created_at

        if sort_order == "asc":
            order_expression = sort_column.asc()
        else:
            order_expression = sort_column.desc()

        query = (
            select(LocalSyncOperation)
            .where(and_(*conditions))
            .order_by(order_expression)
            .offset((page - 1) * page_size)
            .limit(page_size)
        )

        operations = list(
            db.scalars(query).all()
        )

        return operations, total

    def create(
        self,
        db: Session,
        operation: LocalSyncOperation,
    ) -> LocalSyncOperation:
        db.add(operation)
        db.flush()
        db.refresh(operation)
        return operation

    def update(
        self,
        db: Session,
        operation: LocalSyncOperation,
    ) -> LocalSyncOperation:
        db.flush()
        db.refresh(operation)
        return operation