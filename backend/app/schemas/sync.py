from datetime import datetime

from pydantic import BaseModel, Field


class SyncOperationCreate(BaseModel):
    operation_id: str = Field(
        min_length=1,
        max_length=100,
    )

    record_id: int | None = Field(
        default=None,
        ge=1,
    )

    operation_type: str = Field(
        min_length=1,
        max_length=20,
    )

    base_version: int = Field(
        ge=0,
    )

    payload: dict | None = None


class SyncOperationResponse(BaseModel):
    id: int
    operation_id: str
    record_id: int | None
    user_id: int
    operation_type: str
    base_version: int
    payload: dict | None
    status: str
    attempt_count: int
    error_message: str | None
    created_at: datetime
    updated_at: datetime

    model_config = {
        "from_attributes": True,
    }