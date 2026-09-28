import json

from sqlalchemy.orm import Session

from app.models.audit_log import AuditLog
from app.models.user import User
from app.repositories.audit_log_repository import AuditLogRepository


class AuditLogService:

    def __init__(self) -> None:
        self.audit_repository = AuditLogRepository()

    def create_log(
        self,
        db: Session,
        user_id: int | None,
        action: str,
        entity_type: str,
        entity_id: int | str | None = None,
        details: dict | str | None = None,
    ) -> AuditLog:

        if isinstance(details, dict):
            details_value = json.dumps(
                details,
                default=str,
            )
        else:
            details_value = details

        audit_log = AuditLog(
            user_id=user_id,
            action=action,
            entity_type=entity_type,
            entity_id=(
                str(entity_id)
                if entity_id is not None
                else None
            ),
            details=details_value,
        )

        return self.audit_repository.create(
            db=db,
            audit_log=audit_log,
        )

    def get_logs(
        self,
        db: Session,
        current_user: User,
        action: str | None = None,
        entity_type: str | None = None,
        entity_id: str | None = None,
        from_date=None,
        to_date=None,
        page: int = 1,
        page_size: int = 20,
        sort_order: str = "desc",
    ) -> dict:

        logs, total = self.audit_repository.get_all_for_user(
            db=db,
            user_id=current_user.id,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            from_date=from_date,
            to_date=to_date,
            page=page,
            page_size=page_size,
            sort_order=sort_order,
        )

        total_pages = (
            (total + page_size - 1) // page_size
            if total > 0
            else 0
        )

        return {
            "items": logs,
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": total_pages,
        }

    def get_all_logs(
        self,
        db: Session,
        action: str | None = None,
        entity_type: str | None = None,
        entity_id: str | None = None,
        from_date=None,
        to_date=None,
        page: int = 1,
        page_size: int = 20,
        sort_order: str = "desc",
    ) -> dict:

        logs, total = self.audit_repository.get_all(
            db=db,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            from_date=from_date,
            to_date=to_date,
            page=page,
            page_size=page_size,
            sort_order=sort_order,
        )

        total_pages = (
            (total + page_size - 1) // page_size
            if total > 0
            else 0
        )

        return {
            "items": logs,
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": total_pages,
        }