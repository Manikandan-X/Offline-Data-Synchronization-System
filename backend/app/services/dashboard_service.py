from datetime import datetime
from math import ceil

from sqlalchemy.orm import Session

from app.models.local_sync_operation import LocalSyncOperation
from app.models.user import User

from app.repositories.conflict_repository import ConflictRepository
from app.repositories.local_sync_operation_repository import (
    LocalSyncOperationRepository,
)
from app.repositories.record_repository import RecordRepository
from app.repositories.sync_history_repository import SyncHistoryRepository

from app.schemas.dashboard import (
    PaginatedSyncOperationResponse,
    SyncDashboardResponse,
)


class DashboardService:

    def __init__(self) -> None:
        self.record_repository = RecordRepository()

        self.local_sync_operation_repository = (
            LocalSyncOperationRepository()
        )

        self.conflict_repository = ConflictRepository()

        self.sync_history_repository = SyncHistoryRepository()

    def get_sync_dashboard(
        self,
        db: Session,
        current_user: User,
    ) -> SyncDashboardResponse:

        total_records = (
            self.record_repository
            .get_total_count_for_owner(
                db=db,
                owner_id=current_user.id,
            )
        )

        total_operations = (
            self.local_sync_operation_repository
            .get_total_count_for_user(
                db=db,
                user_id=current_user.id,
            )
        )

        pending_operations = (
            self.local_sync_operation_repository
            .get_count_by_status_for_user(
                db=db,
                user_id=current_user.id,
                status="PENDING",
            )
        )

        successful_operations = (
            self.local_sync_operation_repository
            .get_count_by_status_for_user(
                db=db,
                user_id=current_user.id,
                status="SUCCESS",
            )
        )

        failed_operations = (
            self.local_sync_operation_repository
            .get_count_by_status_for_user(
                db=db,
                user_id=current_user.id,
                status="FAILED",
            )
        )

        conflict_operations = (
            self.local_sync_operation_repository
            .get_count_by_status_for_user(
                db=db,
                user_id=current_user.id,
                status="CONFLICT",
            )
        )

        total_conflicts = (
            self.conflict_repository
            .get_total_count_for_user(
                db=db,
                user_id=current_user.id,
            )
        )

        pending_conflicts = (
            self.conflict_repository
            .get_count_by_status_for_user(
                db=db,
                user_id=current_user.id,
                resolution_status="PENDING",
            )
        )

        resolved_conflicts = (
            self.conflict_repository
            .get_count_by_status_for_user(
                db=db,
                user_id=current_user.id,
                resolution_status="RESOLVED",
            )
        )

        last_sync_at = (
            self.sync_history_repository
            .get_last_sync_time_for_user(
                db=db,
                user_id=current_user.id,
            )
        )

        return SyncDashboardResponse(
            total_records=total_records,
            total_operations=total_operations,
            pending_operations=pending_operations,
            successful_operations=successful_operations,
            failed_operations=failed_operations,
            conflict_operations=conflict_operations,
            total_conflicts=total_conflicts,
            pending_conflicts=pending_conflicts,
            resolved_conflicts=resolved_conflicts,
            last_sync_at=last_sync_at,
        )

    def search_sync_operations(
        self,
        db: Session,
        current_user: User,
        operation_id: str | None = None,
        status: str | None = None,
        operation_type: str | None = None,
        from_date: datetime | None = None,
        to_date: datetime | None = None,
        page: int = 1,
        page_size: int = 10,
        sort_by: str = "created_at",
        sort_order: str = "desc",
    ) -> PaginatedSyncOperationResponse:

        operations, total = (
            self.local_sync_operation_repository
            .search_for_user(
                db=db,
                user_id=current_user.id,
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
        )

        total_pages = (
            ceil(total / page_size)
            if total > 0
            else 0
        )

        return PaginatedSyncOperationResponse(
            items=operations,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
        )