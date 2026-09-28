from typing import TYPE_CHECKING

from sqlalchemy import Boolean, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base_class import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.record import Record
    from app.models.user import User


class SyncHistory(Base, TimestampMixin):
    __tablename__ = "sync_history"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        autoincrement=True,
    )

    record_id: Mapped[int] = mapped_column(
        ForeignKey("records.id"),
        nullable=False,
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

    sync_status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        index=True,
    )

    conflict_detected: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        index=True,
    )

    error_message: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    record_version: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    record: Mapped["Record"] = relationship(
        "Record",
    )

    user: Mapped["User"] = relationship(
        "User",
    )
