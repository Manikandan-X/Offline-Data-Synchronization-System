from datetime import datetime

from pydantic import BaseModel


class SyncHistoryResponse(BaseModel):
    id: int
    record_id: int
    user_id: int
    operation_type: str
    sync_status: str
    conflict_detected: bool
    error_message: str | None
    record_version: int | None
    created_at: datetime
    updated_at: datetime

    model_config = {
        "from_attributes": True,
    }