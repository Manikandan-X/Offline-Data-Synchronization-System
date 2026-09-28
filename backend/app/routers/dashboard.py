from datetime import datetime

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.dependencies.auth import get_current_user
from app.models.user import User
from app.schemas.dashboard import (
    PaginatedSyncOperationResponse,
    SyncDashboardResponse,
)
from app.services.dashboard_service import DashboardService


router = APIRouter(
    prefix="/dashboard",
    tags=["Dashboard"],
)

dashboard_service = DashboardService()


@router.get(
    "/sync-statistics",
    response_model=SyncDashboardResponse,
)
def get_sync_statistics(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return dashboard_service.get_sync_dashboard(
        db=db,
        current_user=current_user,
    )


@router.get(
    "/sync-operations",
    response_model=PaginatedSyncOperationResponse,
)
def search_sync_operations(
    operation_id: str | None = Query(
        default=None,
        min_length=1,
        max_length=100,
    ),
    status: str | None = Query(
        default=None,
        min_length=1,
        max_length=20,
    ),
    operation_type: str | None = Query(
        default=None,
        min_length=1,
        max_length=20,
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
        default=10,
        ge=1,
        le=100,
    ),
    sort_by: str = Query(
        default="created_at",
    ),
    sort_order: str = Query(
        default="desc",
    ),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return dashboard_service.search_sync_operations(
        db=db,
        current_user=current_user,
        operation_id=operation_id,
        status=status,
        operation_type=operation_type,
        from_date=from_date,
        to_date=to_date,
        page=page,
        page_size=page_size,
        sort_by=sort_by,
        sort_order=sort_order,
    )