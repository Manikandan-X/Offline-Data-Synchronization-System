from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.dependencies.auth import get_current_user
from app.models.user import User
from app.repositories.sync_history_repository import SyncHistoryRepository
from app.schemas.sync_history import SyncHistoryResponse


router = APIRouter(
    prefix="/sync-history",
    tags=["Sync History"],
)

sync_history_repository = SyncHistoryRepository()


@router.get(
    "",
    response_model=list[SyncHistoryResponse],
)
def get_sync_history(
    limit: int = Query(
        default=100,
        ge=1,
        le=100,
    ),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return sync_history_repository.get_all_for_user(
        db=db,
        user_id=current_user.id,
        limit=limit,
    )