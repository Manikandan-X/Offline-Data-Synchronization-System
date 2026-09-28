from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.dependencies.auth import get_current_user
from app.models.user import User
from app.schemas.sync import (
    SyncOperationCreate,
    SyncOperationResponse,
)
from app.services.sync_service import SyncService


router = APIRouter(
    prefix="/sync",
    tags=["Synchronization"],
)

sync_service = SyncService()


@router.post(
    "/operations",
    response_model=SyncOperationResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_sync_operation(
    operation_data: SyncOperationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return sync_service.create_operation(
        db=db,
        current_user=current_user,
        operation_id=operation_data.operation_id,
        record_id=operation_data.record_id,
        operation_type=operation_data.operation_type,
        base_version=operation_data.base_version,
        payload=operation_data.payload,
    )


@router.get(
    "/operations/pending",
    response_model=list[SyncOperationResponse],
)
def get_pending_sync_operations(
    limit: int = Query(
        default=100,
        ge=1,
        le=100,
    ),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return sync_service.get_pending_operations(
        db=db,
        current_user=current_user,
        limit=limit,
    )


@router.post(
    "/operations/{operation_id}/process",
    response_model=SyncOperationResponse,
)
def process_sync_operation(
    operation_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return sync_service.process_operation(
        db=db,
        current_user=current_user,
        operation_id=operation_id,
    )