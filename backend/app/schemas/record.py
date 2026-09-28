from datetime import datetime

from pydantic import BaseModel, Field


class RecordCreate(BaseModel):
    data: dict = Field(
        min_length=1,
    )


class RecordUpdate(BaseModel):
    data: dict = Field(
        min_length=1,
    )


class RecordResponse(BaseModel):
    id: int
    owner_id: int
    data: dict
    version: int
    is_deleted: bool
    created_at: datetime
    updated_at: datetime

    model_config = {
        "from_attributes": True,
    }