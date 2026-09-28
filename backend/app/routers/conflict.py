from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.dependencies.auth import get_current_user
from app.models.user import User
from app.schemas.conflict import (
    ConflictResponse,
    ConflictResolutionRequest,
)
from app.services.conflict_service import ConflictService


router = APIRouter(
    prefix="/conflicts",
    tags=["Conflicts"],
)

conflict_service = ConflictService()


@router.get(
    "",
    response_model=list[ConflictResponse],
)
def get_conflicts(
    limit: int = Query(
        default=100,
        ge=1,
        le=100,
    ),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return conflict_service.get_conflicts(
        db=db,
        current_user=current_user,
        limit=limit,
    )


@router.get(
    "/pending",
    response_model=list[ConflictResponse],
)
def get_pending_conflicts(
    limit: int = Query(
        default=100,
        ge=1,
        le=100,
    ),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return conflict_service.get_pending_conflicts(
        db=db,
        current_user=current_user,
        limit=limit,
    )


@router.get(
    "/{conflict_id}",
    response_model=ConflictResponse,
)
def get_conflict(
    conflict_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return conflict_service.get_conflict(
        db=db,
        current_user=current_user,
        conflict_id=conflict_id,
    )


@router.post(
    "/{conflict_id}/resolve",
    response_model=ConflictResponse,
)
def resolve_conflict(
    conflict_id: int,
    resolution_data: ConflictResolutionRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return conflict_service.resolve_conflict(
        db=db,
        current_user=current_user,
        conflict_id=conflict_id,
        resolution_strategy=resolution_data.resolution_strategy,
        resolution_notes=resolution_data.resolution_notes,
        resolution_data=resolution_data.resolution_data,
    )