from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.exceptions import (
    BadRequestException,
    ConflictException,
    NotFoundException,
)
from app.core.redis import RedisLockUnavailable, try_sync_lock
from app.models.local_sync_operation import LocalSyncOperation
from app.models.record import Record
from app.models.sync_history import SyncHistory
from app.models.user import User
from app.repositories.local_sync_operation_repository import (
    LocalSyncOperationRepository,
)
from app.repositories.record_repository import RecordRepository
from app.repositories.sync_history_repository import SyncHistoryRepository
from app.services.conflict_service import ConflictService

from app.constants.audit import AuditAction, AuditEntity
from app.services.audit_log_service import AuditLogService


class SyncService:
    ALLOWED_OPERATION_TYPES = {"CREATE", "UPDATE", "DELETE"}

    def __init__(self) -> None:
        self.sync_repository = LocalSyncOperationRepository()
        self.record_repository = RecordRepository()
        self.history_repository = SyncHistoryRepository()
        self.conflict_service = ConflictService()
        self.audit_log_service = AuditLogService()

    def create_operation(
        self,
        db: Session,
        current_user: User,
        operation_id: str,
        record_id: int | None,
        operation_type: str,
        base_version: int,
        payload: dict | None,
    ) -> LocalSyncOperation:

        operation_type = operation_type.upper()

        if operation_type not in self.ALLOWED_OPERATION_TYPES:
            raise BadRequestException(
                "Operation type must be CREATE, UPDATE, or DELETE"
            )

        existing_operation = (
            self.sync_repository.get_by_operation_id_for_user(
                db=db,
                operation_id=operation_id,
                user_id=current_user.id,
            )
        )

        if existing_operation is not None:
            raise ConflictException(
                "Sync operation with this operation_id already exists"
            )

        if operation_type == "CREATE":
            if record_id is not None:
                raise BadRequestException(
                    "record_id must be null for CREATE operations"
                )

            if payload is None or not payload:
                raise BadRequestException(
                    "payload is required for CREATE operations"
                )

        else:
            if record_id is None:
                raise BadRequestException(
                    "record_id is required for UPDATE and DELETE operations"
                )

            record = self.record_repository.get_by_id_for_owner(
                db=db,
                record_id=record_id,
                owner_id=current_user.id,
            )

            if record is None or record.is_deleted:
                raise NotFoundException("Record not found")

        if operation_type == "DELETE" and payload is not None:
            raise BadRequestException(
                "payload must be null for DELETE operations"
            )

        operation = LocalSyncOperation(
            operation_id=operation_id,
            record_id=record_id,
            user_id=current_user.id,
            operation_type=operation_type,
            base_version=base_version,
            payload=payload,
            status="PENDING",
            attempt_count=0,
            error_message=None,
        )

        try:
            operation = self.sync_repository.create(
                db=db,
                operation=operation,
            )
            
            self.audit_log_service.create_log(
                db=db,
                user_id=current_user.id,
                action=AuditAction.SYNC_OPERATION_CREATED,
                entity_type=AuditEntity.SYNC_OPERATION,
                entity_id=operation.operation_id,
                details={
                    "operation_type": operation.operation_type,
                    "record_id": operation.record_id,
                    "base_version": operation.base_version,
                },
            )

            db.commit()
            db.refresh(operation)

            return operation

        except SQLAlchemyError:
            db.rollback()
            raise

    def get_pending_operations(
        self,
        db: Session,
        current_user: User,
        limit: int = 100,
    ) -> list[LocalSyncOperation]:

        return self.sync_repository.get_pending_for_user(
            db=db,
            user_id=current_user.id,
            limit=limit,
        )

    def process_operation(
        self,
        db: Session,
        current_user: User,
        operation_id: str,
    ) -> LocalSyncOperation:

        operation = self.sync_repository.get_by_operation_id_for_user(
            db=db,
            operation_id=operation_id,
            user_id=current_user.id,
        )

        if operation is None:
            raise NotFoundException("Sync operation not found")

        if operation.status == "SUCCESS":
            return operation

        if operation.status == "CONFLICT":
            raise ConflictException(
                "Sync operation has a conflict and cannot be processed"
            )

        try:
            with try_sync_lock(operation_id):

                return self._process_operation_with_mysql(
                    db=db,
                    current_user=current_user,
                    operation_id=operation_id,
                )

        except RedisLockUnavailable as exc:
            raise ConflictException(str(exc))

    def _process_operation_with_mysql(
        self,
        db: Session,
        current_user: User,
        operation_id: str,
    ) -> LocalSyncOperation:

        operation = self.sync_repository.get_by_operation_id_for_user(
            db=db,
            operation_id=operation_id,
            user_id=current_user.id,
        )

        if operation is None:
            raise NotFoundException("Sync operation not found")

        if operation.status == "SUCCESS":
            return operation

        if operation.status == "CONFLICT":
            raise ConflictException(
                "Sync operation has a conflict and cannot be processed"
            )

        operation.status = "PROCESSING"
        operation.attempt_count += 1
        operation.error_message = None

        try:
            if operation.operation_type == "CREATE":
                self._process_create(
                    db=db,
                    operation=operation,
                    current_user=current_user,
                )

            elif operation.operation_type == "UPDATE":
                self._process_update(
                    db=db,
                    operation=operation,
                    current_user=current_user,
                )

            elif operation.operation_type == "DELETE":
                self._process_delete(
                    db=db,
                    operation=operation,
                    current_user=current_user,
                )

            else:
                raise BadRequestException(
                    "Unsupported sync operation type"
                )

            operation.status = "SUCCESS"
            operation.error_message = None

            record_version = None

            if operation.record_id is not None:
                record = self.record_repository.get_by_id_for_owner(
                    db=db,
                    record_id=operation.record_id,
                    owner_id=current_user.id,
                )

                if record is not None:
                    record_version = record.version

            self._create_history(
                db=db,
                operation=operation,
                sync_status="SUCCESS",
                record_version=record_version,
            )

            self.sync_repository.update(
                db=db,
                operation=operation,
            )
            
            self.audit_log_service.create_log(
                db=db,
                user_id=current_user.id,
                action=AuditAction.SYNC_OPERATION_PROCESSED,
                entity_type=AuditEntity.SYNC_OPERATION,
                entity_id=operation.operation_id,
                details={
                    "operation_type": operation.operation_type,
                    "record_id": operation.record_id,
                    "status": operation.status,
                    "record_version": record_version,
                },
            )

            db.commit()
            db.refresh(operation)

            return operation

        except ConflictException:
            db.rollback()
            raise

        except BadRequestException:
            db.rollback()
            raise

        except NotFoundException:
            db.rollback()
            raise

        except SQLAlchemyError:
            db.rollback()

            operation = (
                self.sync_repository.get_by_operation_id_for_user(
                    db=db,
                    operation_id=operation_id,
                    user_id=current_user.id,
                )
            )

            if operation is not None:
                operation.status = "FAILED"
                operation.error_message = "A database error occurred"

                self._create_history(
                    db=db,
                    operation=operation,
                    sync_status="FAILED",
                    error_message=operation.error_message,
                )

                self.sync_repository.update(
                    db=db,
                    operation=operation,
                )
                
                self.audit_log_service.create_log(
                    db=db,
                    user_id=current_user.id,
                    action=AuditAction.SYNC_OPERATION_FAILED,
                    entity_type=AuditEntity.SYNC_OPERATION,
                    entity_id=operation.operation_id,
                    details={
                        "operation_type": operation.operation_type,
                        "record_id": operation.record_id,
                        "error": operation.error_message,
                    },
                )

                db.commit()
                db.refresh(operation)

            raise

        except Exception as exc:
            db.rollback()

            operation = (
                self.sync_repository.get_by_operation_id_for_user(
                    db=db,
                    operation_id=operation_id,
                    user_id=current_user.id,
                )
            )

            if operation is not None:
                operation.status = "FAILED"
                operation.error_message = str(exc)

                self._create_history(
                    db=db,
                    operation=operation,
                    sync_status="FAILED",
                    error_message=operation.error_message,
                )

                self.sync_repository.update(
                    db=db,
                    operation=operation,
                )
                
                self.audit_log_service.create_log(
                    db=db,
                    user_id=current_user.id,
                    action=AuditAction.SYNC_OPERATION_FAILED,
                    entity_type=AuditEntity.SYNC_OPERATION,
                    entity_id=operation.operation_id,
                    details={
                        "operation_type": operation.operation_type,
                        "record_id": operation.record_id,
                        "error": str(exc),
                    },
                )

                db.commit()
                db.refresh(operation)

            raise

    def _process_create(
        self,
        db: Session,
        operation: LocalSyncOperation,
        current_user: User,
    ) -> None:

        if operation.record_id is not None:
            raise BadRequestException(
                "CREATE operation cannot already have a record_id"
            )

        if operation.payload is None or not operation.payload:
            raise BadRequestException(
                "CREATE operation payload is required"
            )

        record_data = operation.payload.get("data")

        if not isinstance(record_data, dict) or not record_data:
            raise BadRequestException(
                "CREATE payload must contain a non-empty data object"
            )

        record = Record(
            owner_id=current_user.id,
            data=record_data,
            version=1,
            is_deleted=False,
        )

        self.record_repository.create(
            db=db,
            record=record,
        )

        operation.record_id = record.id

    def _process_update(
        self,
        db: Session,
        operation: LocalSyncOperation,
        current_user: User,
    ) -> None:

        if operation.record_id is None:
            raise BadRequestException(
                "UPDATE operation requires a record_id"
            )

        if operation.payload is None or not operation.payload:
            raise BadRequestException(
                "UPDATE operation payload is required"
            )

        record = self.record_repository.get_by_id_for_owner(
            db=db,
            record_id=operation.record_id,
            owner_id=current_user.id,
        )

        if record is None or record.is_deleted:
            raise NotFoundException("Record not found")

        self._check_version_conflict(
            db=db,
            operation=operation,
            current_user=current_user,
            record=record,
        )

        record_data = operation.payload.get("data")

        if not isinstance(record_data, dict) or not record_data:
            raise BadRequestException(
                "UPDATE payload must contain a non-empty data object"
            )

        record.data = record_data
        record.version += 1

        self.record_repository.update(
            db=db,
            record=record,
        )

    def _process_delete(
        self,
        db: Session,
        operation: LocalSyncOperation,
        current_user: User,
    ) -> None:

        if operation.record_id is None:
            raise BadRequestException(
                "DELETE operation requires a record_id"
            )

        record = self.record_repository.get_by_id_for_owner(
            db=db,
            record_id=operation.record_id,
            owner_id=current_user.id,
        )

        if record is None or record.is_deleted:
            raise NotFoundException("Record not found")

        self._check_version_conflict(
            db=db,
            operation=operation,
            current_user=current_user,
            record=record,
        )

        record.is_deleted = True
        record.version += 1

        self.record_repository.update(
            db=db,
            record=record,
        )

    def _check_version_conflict(
        self,
        db: Session,
        operation: LocalSyncOperation,
        current_user: User,
        record: Record,
    ) -> None:

        if operation.base_version == record.version:
            return

        self.conflict_service.create_conflict(
            db=db,
            current_user=current_user,
            record_id=record.id,
            client_version=operation.base_version,
            server_version=record.version,
            client_data=(
                operation.payload.get("data")
                if operation.payload
                else None
            ),
            server_data=record.data,
        )

        operation.status = "CONFLICT"
        operation.error_message = (
            "Record version conflict detected"
        )

        self._create_history(
            db=db,
            operation=operation,
            sync_status="CONFLICT",
            conflict_detected=True,
            error_message=operation.error_message,
            record_version=record.version,
        )

        self.sync_repository.update(
            db=db,
            operation=operation,
        )
        
        self.audit_log_service.create_log(
            db=db,
            user_id=current_user.id,
            action=AuditAction.SYNC_OPERATION_CONFLICT,
            entity_type=AuditEntity.SYNC_OPERATION,
            entity_id=operation.operation_id,
            details={
                "record_id": record.id,
                "client_version": operation.base_version,
                "server_version": record.version,
                "status": operation.status,
            },
        )

        db.commit()
        db.refresh(operation)

        raise ConflictException(
            f"Record version conflict detected. "
            f"Client version: {operation.base_version}, "
            f"server version: {record.version}"
        )

    def _create_history(
        self,
        db: Session,
        operation: LocalSyncOperation,
        sync_status: str,
        conflict_detected: bool = False,
        error_message: str | None = None,
        record_version: int | None = None,
    ) -> None:

        if operation.record_id is None:
            return

        history = SyncHistory(
            record_id=operation.record_id,
            user_id=operation.user_id,
            operation_type=operation.operation_type,
            sync_status=sync_status,
            conflict_detected=conflict_detected,
            error_message=error_message,
            record_version=record_version,
        )

        self.history_repository.create(
            db=db,
            history=history,
        )