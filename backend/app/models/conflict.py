from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base_class import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.record import Record
    from app.models.user import User


class Conflict(Base, TimestampMixin):
    __tablename__ = "conflicts"

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

    client_version: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    server_version: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    client_data: Mapped[dict | None] = mapped_column(
        JSON,
        nullable=True,
    )

    server_data: Mapped[dict | None] = mapped_column(
        JSON,
        nullable=True,
    )

    resolution_strategy: Mapped[str | None] = mapped_column(
        String(30),
        nullable=True,
    )

    resolution_status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="PENDING",
        index=True,
    )

    resolution_notes: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    record: Mapped["Record"] = relationship(
        "Record",
    )

    user: Mapped["User"] = relationship(
        "User",
    )
