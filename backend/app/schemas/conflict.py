from datetime import datetime

from pydantic import BaseModel, Field


class ConflictResponse(BaseModel):
    id: int
    record_id: int
    user_id: int
    client_version: int
    server_version: int
    client_data: dict | None
    server_data: dict | None
    resolution_strategy: str | None
    resolution_status: str
    resolution_notes: str | None
    created_at: datetime
    updated_at: datetime

    model_config = {
        "from_attributes": True,
    }


class ConflictResolutionRequest(BaseModel):
    resolution_strategy: str = Field(
        min_length=1,
        max_length=30,
    )
    resolution_notes: str | None = None
    resolution_data: dict | None = None