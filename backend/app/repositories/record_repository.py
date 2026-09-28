from sqlalchemy import func, select

from sqlalchemy.orm import Session

from app.models.record import Record


class RecordRepository:

    def get_by_id(
        self,
        db: Session,
        record_id: int,
    ) -> Record | None:
        return db.get(Record, record_id)

    def get_by_id_for_owner(
        self,
        db: Session,
        record_id: int,
        owner_id: int,
    ) -> Record | None:
        return db.scalar(
            select(Record).where(
                Record.id == record_id,
                Record.owner_id == owner_id,
            )
        )

    def get_all_for_owner(
        self,
        db: Session,
        owner_id: int,
        page: int,
        page_size: int,
    ) -> tuple[list[Record], int]:
        query = (
            select(Record)
            .where(
                Record.owner_id == owner_id,
                Record.is_deleted.is_(False),
            )
            .order_by(Record.id.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )

        count_query = select(func.count(Record.id)).where(
            Record.owner_id == owner_id,
            Record.is_deleted.is_(False),
        )

        records = list(
            db.scalars(query).all()
        )

        total = db.scalar(count_query) or 0

        return records, total

    def get_total_count_for_owner(
        self,
        db: Session,
        owner_id: int,
    ) -> int:
        query = select(
            func.count(Record.id)
        ).where(
            Record.owner_id == owner_id,
            Record.is_deleted.is_(False),
        )

        return db.scalar(query) or 0

    def create(
        self,
        db: Session,
        record: Record,
    ) -> Record:
        db.add(record)
        db.flush()
        db.refresh(record)
        return record

    def update(
        self,
        db: Session,
        record: Record,
    ) -> Record:
        db.flush()
        db.refresh(record)
        return record

    def delete(
        self,
        db: Session,
        record: Record,
    ) -> None:
        db.delete(record)
        db.flush()