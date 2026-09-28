from datetime import datetime

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.audit_log import AuditLog


class AuditLogRepository:

    def get_by_id(
        self,
        db: Session,
        audit_log_id: int,
    ) -> AuditLog | None:
        return db.get(AuditLog, audit_log_id)

    def get_all_for_user(
        self,
        db: Session,
        user_id: int,
        action: str | None = None,
        entity_type: str | None = None,
        entity_id: str | None = None,
        from_date: datetime | None = None,
        to_date: datetime | None = None,
        page: int = 1,
        page_size: int = 20,
        sort_order: str = "desc",
    ) -> tuple[list[AuditLog], int]:

        conditions = [
            AuditLog.user_id == user_id
        ]

        if action is not None:
            conditions.append(
                AuditLog.action == action
            )

        if entity_type is not None:
            conditions.append(
                AuditLog.entity_type == entity_type
            )

        if entity_id is not None:
            conditions.append(
                AuditLog.entity_id == entity_id
            )

        if from_date is not None:
            conditions.append(
                AuditLog.created_at >= from_date
            )

        if to_date is not None:
            conditions.append(
                AuditLog.created_at <= to_date
            )

        count_query = (
            select(func.count(AuditLog.id))
            .where(*conditions)
        )

        total = db.scalar(count_query) or 0

        if sort_order.lower() == "asc":
            order_expression = AuditLog.created_at.asc()
        else:
            order_expression = AuditLog.created_at.desc()

        query = (
            select(AuditLog)
            .where(*conditions)
            .order_by(
                order_expression,
                AuditLog.id.desc(),
            )
            .offset((page - 1) * page_size)
            .limit(page_size)
        )

        logs = list(db.scalars(query).all())

        return logs, total

    def get_all(
        self,
        db: Session,
        action: str | None = None,
        entity_type: str | None = None,
        entity_id: str | None = None,
        from_date: datetime | None = None,
        to_date: datetime | None = None,
        page: int = 1,
        page_size: int = 20,
        sort_order: str = "desc",
    ) -> tuple[list[AuditLog], int]:

        conditions = []

        if action is not None:
            conditions.append(
                AuditLog.action == action
            )

        if entity_type is not None:
            conditions.append(
                AuditLog.entity_type == entity_type
            )

        if entity_id is not None:
            conditions.append(
                AuditLog.entity_id == entity_id
            )

        if from_date is not None:
            conditions.append(
                AuditLog.created_at >= from_date
            )

        if to_date is not None:
            conditions.append(
                AuditLog.created_at <= to_date
            )

        count_query = select(func.count(AuditLog.id))

        if conditions:
            count_query = count_query.where(*conditions)

        total = db.scalar(count_query) or 0

        if sort_order.lower() == "asc":
            order_expression = AuditLog.created_at.asc()
        else:
            order_expression = AuditLog.created_at.desc()

        query = select(AuditLog)

        if conditions:
            query = query.where(*conditions)

        query = (
            query
            .order_by(
                order_expression,
                AuditLog.id.desc(),
            )
            .offset((page - 1) * page_size)
            .limit(page_size)
        )

        logs = list(db.scalars(query).all())

        return logs, total

    def create(
        self,
        db: Session,
        audit_log: AuditLog,
    ) -> AuditLog:

        db.add(audit_log)
        db.flush()
        db.refresh(audit_log)

        return audit_log