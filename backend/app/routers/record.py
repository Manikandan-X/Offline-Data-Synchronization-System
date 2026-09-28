from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.dependencies.auth import get_current_user
from app.models.user import User
from app.schemas.common import PaginatedResponse
from app.schemas.record import (
    RecordCreate,
    RecordResponse,
    RecordUpdate,
)
from app.services.record_service import RecordService


router = APIRouter(
    prefix="/records",
    tags=["Records"],
)

record_service = RecordService()


@router.post(
    "",
    response_model=RecordResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_record(
    record_data: RecordCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return record_service.create_record(
        db=db,
        current_user=current_user,
        data=record_data.data,
    )


@router.get(
    "",
    response_model=PaginatedResponse[RecordResponse],
)
def get_records(
    page: int = Query(
        default=1,
        ge=1,
    ),
    page_size: int = Query(
        default=20,
        ge=1,
        le=100,
    ),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    records, total = record_service.get_records(
        db=db,
        current_user=current_user,
        page=page,
        page_size=page_size,
    )

    total_pages = (
        (total + page_size - 1) // page_size
        if total > 0
        else 0
    )

    return PaginatedResponse[RecordResponse](
        items=records,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )


@router.get(
    "/{record_id}",
    response_model=RecordResponse,
)
def get_record(
    record_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return record_service.get_record(
        db=db,
        current_user=current_user,
        record_id=record_id,
    )


@router.put(
    "/{record_id}",
    response_model=RecordResponse,
)
def update_record(
    record_id: int,
    record_data: RecordUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return record_service.update_record(
        db=db,
        current_user=current_user,
        record_id=record_id,
        data=record_data.data,
    )


@router.delete(
    "/{record_id}",
    response_model=RecordResponse,
)
def delete_record(
    record_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return record_service.delete_record(
        db=db,
        current_user=current_user,
        record_id=record_id,
    )