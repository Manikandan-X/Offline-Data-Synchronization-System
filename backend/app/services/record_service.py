from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundException
from app.models.record import Record
from app.models.user import User
from app.repositories.record_repository import RecordRepository

from app.constants.audit import AuditAction, AuditEntity
from app.services.audit_log_service import AuditLogService


class RecordService:

    def __init__(self) -> None:
        self.record_repository = RecordRepository()
        self.audit_log_service = AuditLogService()

    def create_record(
        self,
        db: Session,
        current_user: User,
        data: dict,
    ) -> Record:

        record = Record(
            owner_id=current_user.id,
            data=data,
            version=1,
            is_deleted=False,
        )

        try:
            record = self.record_repository.create(
                db=db,
                record=record,
            )
            
            self.audit_log_service.create_log(
                db=db,
                user_id=current_user.id,
                action=AuditAction.RECORD_CREATED,
                entity_type=AuditEntity.RECORD,
                entity_id=record.id,
                details={
                    "version": record.version,
                },
            )

            db.commit()
            db.refresh(record)

            return record

        except SQLAlchemyError:
            db.rollback()
            raise

    def get_record(
        self,
        db: Session,
        current_user: User,
        record_id: int,
    ) -> Record:

        record = self.record_repository.get_by_id_for_owner(
            db=db,
            record_id=record_id,
            owner_id=current_user.id,
        )

        if record is None or record.is_deleted:
            raise NotFoundException("Record not found")

        return record

    def get_records(
        self,
        db: Session,
        current_user: User,
        page: int,
        page_size: int,
    ) -> tuple[list[Record], int]:

        return self.record_repository.get_all_for_owner(
            db=db,
            owner_id=current_user.id,
            page=page,
            page_size=page_size,
        )

    def update_record(
        self,
        db: Session,
        current_user: User,
        record_id: int,
        data: dict,
    ) -> Record:

        record = self.record_repository.get_by_id_for_owner(
            db=db,
            record_id=record_id,
            owner_id=current_user.id,
        )

        if record is None or record.is_deleted:
            raise NotFoundException("Record not found")

        record.data = data
        record.version += 1

        try:
            record = self.record_repository.update(
                db=db,
                record=record,
            )
            
            self.audit_log_service.create_log(
                db=db,
                user_id=current_user.id,
                action=AuditAction.RECORD_UPDATED,
                entity_type=AuditEntity.RECORD,
                entity_id=record.id,
                details={
                    "version": record.version,
                },
            )

            db.commit()
            db.refresh(record)

            return record

        except SQLAlchemyError:
            db.rollback()
            raise

    def delete_record(
        self,
        db: Session,
        current_user: User,
        record_id: int,
    ) -> Record:

        record = self.record_repository.get_by_id_for_owner(
            db=db,
            record_id=record_id,
            owner_id=current_user.id,
        )

        if record is None or record.is_deleted:
            raise NotFoundException("Record not found")

        record.is_deleted = True
        record.version += 1

        try:
            record = self.record_repository.update(
                db=db,
                record=record,
            )
            
            self.audit_log_service.create_log(
                db=db,
                user_id=current_user.id,
                action=AuditAction.RECORD_DELETED,
                entity_type=AuditEntity.RECORD,
                entity_id=record.id,
                details={
                    "version": record.version,
                },
            )

            db.commit()
            db.refresh(record)

            return record

        except SQLAlchemyError:
            db.rollback()
            raise