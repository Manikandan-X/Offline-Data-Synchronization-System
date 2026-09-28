from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.exceptions import (
    BadRequestException,
    NotFoundException,
)
from app.models.conflict import Conflict
from app.models.user import User
from app.repositories.conflict_repository import ConflictRepository
from app.repositories.record_repository import RecordRepository

from app.constants.audit import AuditAction, AuditEntity
from app.services.audit_log_service import AuditLogService


class ConflictService:
    ALLOWED_RESOLUTION_STRATEGIES = {
        "SERVER_WINS",
        "CLIENT_WINS",
        "LAST_WRITE_WINS",
        "MANUAL",
    }

    def __init__(self) -> None:
        self.conflict_repository = ConflictRepository()
        self.record_repository = RecordRepository()
        self.audit_log_service = AuditLogService()

    def get_conflict(
        self,
        db: Session,
        current_user: User,
        conflict_id: int,
    ) -> Conflict:
        conflict = self.conflict_repository.get_by_id_for_user(
            db=db,
            conflict_id=conflict_id,
            user_id=current_user.id,
        )

        if conflict is None:
            raise NotFoundException("Conflict not found")

        return conflict

    def get_conflicts(
        self,
        db: Session,
        current_user: User,
        limit: int = 100,
    ) -> list[Conflict]:
        return self.conflict_repository.get_all_for_user(
            db=db,
            user_id=current_user.id,
            limit=limit,
        )

    def get_pending_conflicts(
        self,
        db: Session,
        current_user: User,
        limit: int = 100,
    ) -> list[Conflict]:
        return self.conflict_repository.get_pending_for_user(
            db=db,
            user_id=current_user.id,
            limit=limit,
        )

    def create_conflict(
        self,
        db: Session,
        current_user: User,
        record_id: int,
        client_version: int,
        server_version: int,
        client_data: dict | None,
        server_data: dict | None,
    ) -> Conflict:
        if client_version < 0:
            raise BadRequestException(
                "Client version cannot be negative"
            )

        if server_version < 0:
            raise BadRequestException(
                "Server version cannot be negative"
            )

        if client_version >= server_version:
            raise BadRequestException(
                "Conflict requires client version to be older than server version"
            )

        conflict = Conflict(
            record_id=record_id,
            user_id=current_user.id,
            client_version=client_version,
            server_version=server_version,
            client_data=client_data,
            server_data=server_data,
            resolution_strategy=None,
            resolution_status="PENDING",
            resolution_notes=None,
        )

        try:
            conflict = self.conflict_repository.create(
                db=db,
                conflict=conflict,
            )
            
            self.audit_log_service.create_log(
                db=db,
                user_id=current_user.id,
                action=AuditAction.CONFLICT_CREATED,
                entity_type=AuditEntity.CONFLICT,
                entity_id=conflict.id,
                details={
                    "record_id": conflict.record_id,
                    "client_version": conflict.client_version,
                    "server_version": conflict.server_version,
                },
            )

            db.commit()
            db.refresh(conflict)

            return conflict

        except SQLAlchemyError:
            db.rollback()
            raise

    def resolve_conflict(
        self,
        db: Session,
        current_user: User,
        conflict_id: int,
        resolution_strategy: str,
        resolution_notes: str | None = None,
        resolution_data: dict | None = None,
    ) -> Conflict:

        resolution_strategy = resolution_strategy.upper()

        if resolution_strategy not in self.ALLOWED_RESOLUTION_STRATEGIES:
            raise BadRequestException(
                "Resolution strategy must be SERVER_WINS, CLIENT_WINS, LAST_WRITE_WINS, or MANUAL"
            )

        conflict = self.conflict_repository.get_by_id_for_user(
            db=db,
            conflict_id=conflict_id,
            user_id=current_user.id,
        )

        if conflict is None:
            raise NotFoundException("Conflict not found")

        if conflict.resolution_status == "RESOLVED":
            raise BadRequestException(
                "Conflict has already been resolved"
            )

        record = self.record_repository.get_by_id_for_owner(
            db=db,
            record_id=conflict.record_id,
            owner_id=current_user.id,
        )

        if record is None:
            raise NotFoundException("Record not found")

        if record.is_deleted:
            raise NotFoundException("Record not found")

        # -----------------------------------------
        # MANUAL RESOLUTION
        # -----------------------------------------
        if resolution_strategy == "MANUAL":

            if resolution_data is None:
                raise BadRequestException(
                    "Resolution data is required for MANUAL resolution"
                )

            if not isinstance(resolution_data, dict):
                raise BadRequestException(
                    "Resolution data must be an object"
                )

            selected_data = resolution_data

        # -----------------------------------------
        # SERVER WINS
        # -----------------------------------------
        elif resolution_strategy == "SERVER_WINS":

            selected_data = conflict.server_data

            if selected_data is None:
                raise BadRequestException(
                    "Selected conflict data is empty"
                )

        # -----------------------------------------
        # CLIENT WINS
        # -----------------------------------------
        elif resolution_strategy == "CLIENT_WINS":

            selected_data = conflict.client_data

            if selected_data is None:
                raise BadRequestException(
                    "Selected conflict data is empty"
                )

        # -----------------------------------------
        # LAST WRITE WINS
        # -----------------------------------------
        elif resolution_strategy == "LAST_WRITE_WINS":

            if conflict.server_version >= conflict.client_version:
                selected_data = conflict.server_data
            else:
                selected_data = conflict.client_data

            if selected_data is None:
                raise BadRequestException(
                    "Selected conflict data is empty"
                )

        else:
            raise BadRequestException(
                "Unsupported resolution strategy"
            )

        if not isinstance(selected_data, dict):
            raise BadRequestException(
                "Selected conflict data must be an object"
            )

        # -----------------------------------------
        # APPLY RESOLUTION TO RECORD
        # -----------------------------------------

        record.data = selected_data

        # Resolving a conflict creates a new server state,
        # so always move to the next version.
        record.version = record.version + 1

        conflict.resolution_strategy = resolution_strategy
        conflict.resolution_status = "RESOLVED"
        conflict.resolution_notes = resolution_notes

        try:
            self.record_repository.update(
                db=db,
                record=record,
            )

            self.conflict_repository.update(
                db=db,
                conflict=conflict,
            )
            
            self.audit_log_service.create_log(
                db=db,
                user_id=current_user.id,
                action=AuditAction.CONFLICT_RESOLVED,
                entity_type=AuditEntity.CONFLICT,
                entity_id=conflict.id,
                details={
                    "record_id": conflict.record_id,
                    "resolution_strategy": resolution_strategy,
                    "record_version": record.version,
                },
            )

            db.commit()

            db.refresh(record)
            db.refresh(conflict)

            return conflict

        except SQLAlchemyError:
            db.rollback()
            raise