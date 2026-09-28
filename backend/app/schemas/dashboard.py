from datetime import datetime

from pydantic import BaseModel, Field


class SyncDashboardResponse(BaseModel):

    total_records: int = Field(ge=0)

    total_operations: int = Field(ge=0)

    pending_operations: int = Field(ge=0)

    successful_operations: int = Field(ge=0)

    failed_operations: int = Field(ge=0)

    conflict_operations: int = Field(ge=0)

    total_conflicts: int = Field(ge=0)

    pending_conflicts: int = Field(ge=0)

    resolved_conflicts: int = Field(ge=0)

    last_sync_at: datetime | None = None


class SyncOperationDashboardResponse(BaseModel):

    id: int

    operation_id: str

    record_id: int | None

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


class PaginatedSyncOperationResponse(BaseModel):

    items: list[SyncOperationDashboardResponse]

    total: int = Field(ge=0)

    page: int = Field(ge=1)

    page_size: int = Field(ge=1)

    total_pages: int = Field(ge=0)