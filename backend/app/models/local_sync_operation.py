from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base_class import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.record import Record
    from app.models.user import User


class LocalSyncOperation(Base, TimestampMixin):
    __tablename__ = "local_sync_operations"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        autoincrement=True,
    )

    operation_id: Mapped[str] = mapped_column(
        String(100),
        unique=True,
        nullable=False,
        index=True,
    )

    record_id: Mapped[int | None] = mapped_column(
        ForeignKey("records.id"),
        nullable=True,
        index=True,
    )

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"),
        nullable=False,
        index=True,
    )

    operation_type: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
    )

    base_version: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    payload: Mapped[dict | None] = mapped_column(
        JSON,
        nullable=True,
    )

    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="PENDING",
        index=True,
    )

    attempt_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )

    error_message: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    record: Mapped["Record | None"] = relationship(
        "Record",
    )

    user: Mapped["User"] = relationship(
        "User",
    )