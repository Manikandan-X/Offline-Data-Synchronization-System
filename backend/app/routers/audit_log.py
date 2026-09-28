from datetime import datetime

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.dependencies.auth import get_current_user, require_admin
from app.models.user import User
from app.schemas.audit_log import PaginatedAuditLogResponse
from app.services.audit_log_service import AuditLogService


router = APIRouter(
    prefix="/audit-logs",
    tags=["Audit Logs"],
)

audit_log_service = AuditLogService()


@router.get(
    "",
    response_model=PaginatedAuditLogResponse,
)
def get_my_audit_logs(
    action: str | None = Query(
        default=None,
        max_length=100,
    ),
    entity_type: str | None = Query(
        default=None,
        max_length=50,
    ),
    entity_id: str | None = Query(
        default=None,
        max_length=100,
    ),
    from_date: datetime | None = Query(
        default=None,
    ),
    to_date: datetime | None = Query(
        default=None,
    ),
    page: int = Query(
        default=1,
        ge=1,
    ),
    page_size: int = Query(
        default=20,
        ge=1,
        le=100,
    ),
    sort_order: str = Query(
        default="desc",
        pattern="^(asc|desc)$",
    ),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return audit_log_service.get_logs(
        db=db,
        current_user=current_user,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        from_date=from_date,
        to_date=to_date,
        page=page,
        page_size=page_size,
        sort_order=sort_order,
    )


@router.get(
    "/all",
    response_model=PaginatedAuditLogResponse,
)
def get_all_audit_logs(
    action: str | None = Query(
        default=None,
        max_length=100,
    ),
    entity_type: str | None = Query(
        default=None,
        max_length=50,
    ),
    entity_id: str | None = Query(
        default=None,
        max_length=100,
    ),
    from_date: datetime | None = Query(
        default=None,
    ),
    to_date: datetime | None = Query(
        default=None,
    ),
    page: int = Query(
        default=1,
        ge=1,
    ),
    page_size: int = Query(
        default=20,
        ge=1,
        le=100,
    ),
    sort_order: str = Query(
        default="desc",
        pattern="^(asc|desc)$",
    ),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    return audit_log_service.get_all_logs(
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