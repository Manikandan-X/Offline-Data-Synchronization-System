"""Unit tests for SyncService: operation registration and processing."""
import pytest
from sqlalchemy.exc import OperationalError

from app.core.exceptions import (
    BadRequestException,
    ConflictException,
    NotFoundException,
)
from app.core.redis import SYNC_LOCK_PREFIX
from app.models.audit_log import AuditLog
from app.models.conflict import Conflict
from app.models.local_sync_operation import LocalSyncOperation
from app.models.record import Record
from app.models.sync_history import SyncHistory


def _register(sync_service, db, user, op_id, op_type, record_id=None,
              base_version=0, payload=None):
    return sync_service.create_operation(
        db=db,
        current_user=user,
        operation_id=op_id,
        record_id=record_id,
        operation_type=op_type,
        base_version=base_version,
        payload=payload,
    )


def _audit_actions(db):
    return [a.action for a in db.query(AuditLog).order_by(AuditLog.id)]


# ---------------------------------------------------------------------------
# create_operation
# ---------------------------------------------------------------------------
class TestCreateOperation:
    def test_create_operation_is_stored_as_pending(self, db, user, sync_service):
        op = _register(sync_service, db, user, "op-1", "CREATE",
                       payload={"data": {"title": "hello"}})

        assert op.status == "PENDING"
        assert op.attempt_count == 0
        assert op.error_message is None
        assert op.user_id == user.id
        assert op.record_id is None

    def test_operation_type_is_case_insensitive(self, db, user, sync_service):
        op = _register(sync_service, db, user, "op-1", "create",
                       payload={"data": {"a": 1}})
        assert op.operation_type == "CREATE"

    def test_creating_an_operation_writes_an_audit_log(self, db, user, sync_service):
        _register(sync_service, db, user, "op-1", "CREATE",
                  payload={"data": {"a": 1}})
        assert "SYNC_OPERATION_CREATED" in _audit_actions(db)

    def test_unknown_operation_type_is_rejected(self, db, user, sync_service):
        with pytest.raises(BadRequestException):
            _register(sync_service, db, user, "op-1", "UPSERT",
                      payload={"data": {"a": 1}})

    def test_duplicate_operation_id_is_rejected(self, db, user, sync_service):
        _register(sync_service, db, user, "op-1", "CREATE",
                  payload={"data": {"a": 1}})
        with pytest.raises(ConflictException):
            _register(sync_service, db, user, "op-1", "CREATE",
                      payload={"data": {"a": 1}})
        assert db.query(LocalSyncOperation).count() == 1

    @pytest.mark.xfail(
        strict=True,
        reason=(
            "operation_id is globally unique in the DB but the duplicate check "
            "is per-user, so a cross-user collision surfaces as a raw "
            "IntegrityError instead of a clean 409."
        ),
    )
    def test_same_operation_id_from_another_user_is_rejected_cleanly(
        self, db, user, other_user, sync_service
    ):
        _register(sync_service, db, user, "op-1", "CREATE",
                  payload={"data": {"a": 1}})
        with pytest.raises(ConflictException):
            _register(sync_service, db, other_user, "op-1", "CREATE",
                      payload={"data": {"a": 1}})

    def test_create_must_not_carry_a_record_id(self, db, user, sync_service):
        with pytest.raises(BadRequestException):
            _register(sync_service, db, user, "op-1", "CREATE", record_id=5,
                      payload={"data": {"a": 1}})

    @pytest.mark.parametrize("payload", [None, {}])
    def test_create_requires_a_payload(self, db, user, sync_service, payload):
        with pytest.raises(BadRequestException):
            _register(sync_service, db, user, "op-1", "CREATE", payload=payload)

    @pytest.mark.parametrize("op_type", ["UPDATE", "DELETE"])
    def test_update_and_delete_require_a_record_id(self, db, user, sync_service, op_type):
        with pytest.raises(BadRequestException):
            _register(sync_service, db, user, "op-1", op_type,
                      payload={"data": {"a": 1}} if op_type == "UPDATE" else None)

    def test_delete_must_not_carry_a_payload(self, db, user, make_record, sync_service):
        record = make_record(user)
        with pytest.raises(BadRequestException):
            _register(sync_service, db, user, "op-1", "DELETE",
                      record_id=record.id, base_version=1,
                      payload={"data": {"a": 1}})

    def test_update_of_missing_record_is_not_found(self, db, user, sync_service):
        with pytest.raises(NotFoundException):
            _register(sync_service, db, user, "op-1", "UPDATE", record_id=999,
                      base_version=1, payload={"data": {"a": 1}})

    def test_update_of_another_users_record_is_not_found(
        self, db, user, other_user, make_record, sync_service
    ):
        record = make_record(other_user)
        with pytest.raises(NotFoundException):
            _register(sync_service, db, user, "op-1", "UPDATE",
                      record_id=record.id, base_version=1,
                      payload={"data": {"a": 1}})

    def test_update_of_soft_deleted_record_is_not_found(
        self, db, user, make_record, sync_service
    ):
        record = make_record(user, is_deleted=True)
        with pytest.raises(NotFoundException):
            _register(sync_service, db, user, "op-1", "UPDATE",
                      record_id=record.id, base_version=1,
                      payload={"data": {"a": 1}})


# ---------------------------------------------------------------------------
# process_operation - happy paths
# ---------------------------------------------------------------------------
class TestProcessOperation:
    def test_create_builds_a_version_1_record_owned_by_the_user(
        self, db, user, sync_service
    ):
        _register(sync_service, db, user, "op-1", "CREATE",
                  payload={"data": {"title": "hello"}})

        op = sync_service.process_operation(db, user, "op-1")

        record = db.get(Record, op.record_id)
        assert op.status == "SUCCESS"
        assert op.attempt_count == 1
        assert record.owner_id == user.id
        assert record.version == 1
        assert record.data == {"title": "hello"}
        assert record.is_deleted is False

    def test_update_at_matching_version_bumps_version_and_replaces_data(
        self, db, user, make_record, sync_service
    ):
        record = make_record(user, data={"title": "old"}, version=1)
        _register(sync_service, db, user, "op-1", "UPDATE", record_id=record.id,
                  base_version=1, payload={"data": {"title": "new"}})

        op = sync_service.process_operation(db, user, "op-1")

        db.refresh(record)
        assert op.status == "SUCCESS"
        assert record.version == 2
        assert record.data == {"title": "new"}

    def test_delete_at_matching_version_soft_deletes(
        self, db, user, make_record, sync_service
    ):
        record = make_record(user, version=3)
        _register(sync_service, db, user, "op-1", "DELETE", record_id=record.id,
                  base_version=3)

        op = sync_service.process_operation(db, user, "op-1")

        db.refresh(record)
        assert op.status == "SUCCESS"
        assert record.is_deleted is True
        assert record.version == 4
        assert db.get(Record, record.id) is not None  # row is kept, not removed

    def test_success_writes_history_and_audit_log(
        self, db, user, make_record, sync_service
    ):
        record = make_record(user, version=1)
        _register(sync_service, db, user, "op-1", "UPDATE", record_id=record.id,
                  base_version=1, payload={"data": {"title": "new"}})

        sync_service.process_operation(db, user, "op-1")

        history = db.query(SyncHistory).one()
        assert history.record_id == record.id
        assert history.operation_type == "UPDATE"
        assert history.sync_status == "SUCCESS"
        assert history.conflict_detected is False
        assert history.record_version == 2
        assert "SYNC_OPERATION_PROCESSED" in _audit_actions(db)

    def test_create_history_is_recorded_against_the_new_record(
        self, db, user, sync_service
    ):
        _register(sync_service, db, user, "op-1", "CREATE",
                  payload={"data": {"title": "hello"}})
        op = sync_service.process_operation(db, user, "op-1")

        history = db.query(SyncHistory).one()
        assert history.record_id == op.record_id
        assert history.record_version == 1

    def test_operations_apply_in_sequence_when_each_uses_the_latest_version(
        self, db, user, sync_service
    ):
        _register(sync_service, db, user, "op-1", "CREATE",
                  payload={"data": {"n": 1}})
        created = sync_service.process_operation(db, user, "op-1")

        _register(sync_service, db, user, "op-2", "UPDATE",
                  record_id=created.record_id, base_version=1,
                  payload={"data": {"n": 2}})
        sync_service.process_operation(db, user, "op-2")

        _register(sync_service, db, user, "op-3", "UPDATE",
                  record_id=created.record_id, base_version=2,
                  payload={"data": {"n": 3}})
        sync_service.process_operation(db, user, "op-3")

        record = db.get(Record, created.record_id)
        assert record.version == 3
        assert record.data == {"n": 3}


# ---------------------------------------------------------------------------
# process_operation - idempotency / duplicate protection
# ---------------------------------------------------------------------------
class TestIdempotency:
    def test_reprocessing_a_successful_operation_is_a_no_op(
        self, db, user, sync_service
    ):
        _register(sync_service, db, user, "op-1", "CREATE",
                  payload={"data": {"title": "hello"}})

        first = sync_service.process_operation(db, user, "op-1")
        second = sync_service.process_operation(db, user, "op-1")

        assert first.record_id == second.record_id
        assert second.attempt_count == 1
        assert db.query(Record).count() == 1
        assert db.query(SyncHistory).count() == 1

    def test_reprocessing_an_update_does_not_bump_the_version_twice(
        self, db, user, make_record, sync_service
    ):
        record = make_record(user, version=1)
        _register(sync_service, db, user, "op-1", "UPDATE", record_id=record.id,
                  base_version=1, payload={"data": {"title": "new"}})

        sync_service.process_operation(db, user, "op-1")
        sync_service.process_operation(db, user, "op-1")

        db.refresh(record)
        assert record.version == 2

    def test_unknown_operation_is_not_found(self, db, user, sync_service):
        with pytest.raises(NotFoundException):
            sync_service.process_operation(db, user, "does-not-exist")

    def test_cannot_process_another_users_operation(
        self, db, user, other_user, sync_service
    ):
        _register(sync_service, db, user, "op-1", "CREATE",
                  payload={"data": {"a": 1}})
        with pytest.raises(NotFoundException):
            sync_service.process_operation(db, other_user, "op-1")


# ---------------------------------------------------------------------------
# process_operation - version conflicts
# ---------------------------------------------------------------------------
class TestVersionConflicts:
    def test_stale_update_raises_and_creates_a_conflict(
        self, db, user, make_record, sync_service
    ):
        record = make_record(user, data={"title": "server"}, version=3)
        _register(sync_service, db, user, "op-1", "UPDATE", record_id=record.id,
                  base_version=1, payload={"data": {"title": "client"}})

        with pytest.raises(ConflictException):
            sync_service.process_operation(db, user, "op-1")

        conflict = db.query(Conflict).one()
        assert conflict.record_id == record.id
        assert conflict.user_id == user.id
        assert conflict.client_version == 1
        assert conflict.server_version == 3
        assert conflict.client_data == {"title": "client"}
        assert conflict.server_data == {"title": "server"}
        assert conflict.resolution_status == "PENDING"
        assert conflict.resolution_strategy is None

    def test_stale_update_leaves_the_record_untouched(
        self, db, user, make_record, sync_service
    ):
        record = make_record(user, data={"title": "server"}, version=3)
        _register(sync_service, db, user, "op-1", "UPDATE", record_id=record.id,
                  base_version=1, payload={"data": {"title": "client"}})

        with pytest.raises(ConflictException):
            sync_service.process_operation(db, user, "op-1")

        db.refresh(record)
        assert record.data == {"title": "server"}
        assert record.version == 3

    def test_conflicting_operation_is_marked_and_history_flags_it(
        self, db, user, make_record, sync_service
    ):
        record = make_record(user, version=2)
        _register(sync_service, db, user, "op-1", "UPDATE", record_id=record.id,
                  base_version=1, payload={"data": {"title": "client"}})

        with pytest.raises(ConflictException):
            sync_service.process_operation(db, user, "op-1")

        op = db.query(LocalSyncOperation).one()
        assert op.status == "CONFLICT"
        assert op.error_message == "Record version conflict detected"

        history = db.query(SyncHistory).one()
        assert history.sync_status == "CONFLICT"
        assert history.conflict_detected is True
        assert history.record_version == 2

        actions = _audit_actions(db)
        assert "SYNC_OPERATION_CONFLICT" in actions
        assert "CONFLICT_CREATED" in actions

    def test_stale_delete_conflicts_and_does_not_delete(
        self, db, user, make_record, sync_service
    ):
        record = make_record(user, version=2)
        _register(sync_service, db, user, "op-1", "DELETE", record_id=record.id,
                  base_version=1)

        with pytest.raises(ConflictException):
            sync_service.process_operation(db, user, "op-1")

        db.refresh(record)
        assert record.is_deleted is False
        assert record.version == 2
        assert db.query(Conflict).count() == 1

    def test_two_devices_editing_the_same_version_second_one_conflicts(
        self, db, user, make_record, sync_service
    ):
        record = make_record(user, data={"title": "v1"}, version=1)
        _register(sync_service, db, user, "device-a", "UPDATE",
                  record_id=record.id, base_version=1,
                  payload={"data": {"title": "from A"}})
        _register(sync_service, db, user, "device-b", "UPDATE",
                  record_id=record.id, base_version=1,
                  payload={"data": {"title": "from B"}})

        sync_service.process_operation(db, user, "device-a")
        with pytest.raises(ConflictException):
            sync_service.process_operation(db, user, "device-b")

        db.refresh(record)
        assert record.data == {"title": "from A"}
        assert record.version == 2

        conflict = db.query(Conflict).one()
        assert conflict.client_data == {"title": "from B"}
        assert conflict.server_data == {"title": "from A"}

    def test_processing_a_conflicted_operation_again_is_refused(
        self, db, user, make_record, sync_service
    ):
        record = make_record(user, version=2)
        _register(sync_service, db, user, "op-1", "UPDATE", record_id=record.id,
                  base_version=1, payload={"data": {"title": "client"}})
        with pytest.raises(ConflictException):
            sync_service.process_operation(db, user, "op-1")

        with pytest.raises(ConflictException):
            sync_service.process_operation(db, user, "op-1")

        assert db.query(Conflict).count() == 1  # no duplicate conflict rows

    def test_client_ahead_of_server_cannot_be_recorded_as_a_conflict(
        self, db, user, make_record, sync_service
    ):
        """
        Characterization test. base_version > server version is not a
        conflict by ConflictService's definition (it requires client < server),
        so the sync is rejected as a bad request and nothing is written.
        """
        record = make_record(user, version=1)
        _register(sync_service, db, user, "op-1", "UPDATE", record_id=record.id,
                  base_version=5, payload={"data": {"title": "client"}})

        with pytest.raises(BadRequestException):
            sync_service.process_operation(db, user, "op-1")

        db.refresh(record)
        assert record.version == 1
        assert db.query(Conflict).count() == 0


# ---------------------------------------------------------------------------
# process_operation - validation failures roll back cleanly
# ---------------------------------------------------------------------------
class TestProcessingFailures:
    def test_create_with_malformed_payload_creates_no_record(
        self, db, user, sync_service
    ):
        _register(sync_service, db, user, "op-1", "CREATE",
                  payload={"wrong_key": {"a": 1}})

        with pytest.raises(BadRequestException):
            sync_service.process_operation(db, user, "op-1")

        assert db.query(Record).count() == 0
        assert db.query(SyncHistory).count() == 0

    def test_update_with_malformed_payload_leaves_record_unchanged(
        self, db, user, make_record, sync_service
    ):
        record = make_record(user, data={"title": "old"}, version=1)
        _register(sync_service, db, user, "op-1", "UPDATE", record_id=record.id,
                  base_version=1, payload={"data": "not-an-object"})

        with pytest.raises(BadRequestException):
            sync_service.process_operation(db, user, "op-1")

        db.refresh(record)
        assert record.data == {"title": "old"}
        assert record.version == 1

    def test_record_deleted_after_registration_is_not_found_on_processing(
        self, db, user, make_record, sync_service
    ):
        record = make_record(user, version=1)
        _register(sync_service, db, user, "op-1", "UPDATE", record_id=record.id,
                  base_version=1, payload={"data": {"title": "new"}})
        record.is_deleted = True
        db.commit()

        with pytest.raises(NotFoundException):
            sync_service.process_operation(db, user, "op-1")

    def test_database_error_marks_operation_failed_and_records_history(
        self, db, user, make_record, sync_service, monkeypatch
    ):
        record = make_record(user, version=1)
        _register(sync_service, db, user, "op-1", "UPDATE", record_id=record.id,
                  base_version=1, payload={"data": {"title": "new"}})

        def boom(*args, **kwargs):
            raise OperationalError("UPDATE records", {}, Exception("db down"))

        monkeypatch.setattr(sync_service.record_repository, "update", boom)

        with pytest.raises(OperationalError):
            sync_service.process_operation(db, user, "op-1")

        op = db.query(LocalSyncOperation).one()
        assert op.status == "FAILED"
        assert op.error_message == "A database error occurred"

        history = db.query(SyncHistory).one()
        assert history.sync_status == "FAILED"
        assert history.error_message == "A database error occurred"
        assert "SYNC_OPERATION_FAILED" in _audit_actions(db)

        db.refresh(record)
        assert record.version == 1  # the partial write was rolled back

    def test_unexpected_error_marks_operation_failed_with_its_message(
        self, db, user, make_record, sync_service, monkeypatch
    ):
        record = make_record(user, version=1)
        _register(sync_service, db, user, "op-1", "UPDATE", record_id=record.id,
                  base_version=1, payload={"data": {"title": "new"}})

        def boom(*args, **kwargs):
            raise RuntimeError("something odd")

        monkeypatch.setattr(sync_service.record_repository, "update", boom)

        with pytest.raises(RuntimeError):
            sync_service.process_operation(db, user, "op-1")

        op = db.query(LocalSyncOperation).one()
        assert op.status == "FAILED"
        assert op.error_message == "something odd"

    @pytest.mark.xfail(
        strict=True,
        reason=(
            "The failure path re-fetches the operation after rollback, which "
            "discards the in-memory attempt_count += 1, so failed attempts are "
            "never counted."
        ),
    )
    def test_failed_attempts_are_counted(
        self, db, user, make_record, sync_service, monkeypatch
    ):
        record = make_record(user, version=1)
        _register(sync_service, db, user, "op-1", "UPDATE", record_id=record.id,
                  base_version=1, payload={"data": {"title": "new"}})
        monkeypatch.setattr(
            sync_service.record_repository, "update",
            lambda *a, **k: (_ for _ in ()).throw(RuntimeError("fail")),
        )

        with pytest.raises(RuntimeError):
            sync_service.process_operation(db, user, "op-1")

        assert db.query(LocalSyncOperation).one().attempt_count == 1

    def test_a_failed_operation_can_be_retried_successfully(
        self, db, user, make_record, sync_service, monkeypatch
    ):
        record = make_record(user, version=1)
        _register(sync_service, db, user, "op-1", "UPDATE", record_id=record.id,
                  base_version=1, payload={"data": {"title": "new"}})

        original_update = sync_service.record_repository.update
        monkeypatch.setattr(
            sync_service.record_repository, "update",
            lambda *a, **k: (_ for _ in ()).throw(RuntimeError("transient")),
        )
        with pytest.raises(RuntimeError):
            sync_service.process_operation(db, user, "op-1")

        monkeypatch.setattr(sync_service.record_repository, "update", original_update)
        op = sync_service.process_operation(db, user, "op-1")

        db.refresh(record)
        assert op.status == "SUCCESS"
        assert record.version == 2


# ---------------------------------------------------------------------------
# Redis lock coordination inside process_operation
# ---------------------------------------------------------------------------
class TestProcessingLock:
    def test_operation_held_by_another_worker_is_refused_untouched(
        self, db, user, make_record, sync_service, fake_redis
    ):
        record = make_record(user, version=1)
        _register(sync_service, db, user, "op-1", "UPDATE", record_id=record.id,
                  base_version=1, payload={"data": {"title": "new"}})
        fake_redis.store[f"{SYNC_LOCK_PREFIX}op-1"] = "another-worker-token"

        with pytest.raises(ConflictException):
            sync_service.process_operation(db, user, "op-1")

        db.refresh(record)
        op = db.query(LocalSyncOperation).one()
        assert record.version == 1
        assert op.status == "PENDING"
        assert op.attempt_count == 0
        # the other worker's lock must not be stolen or released
        assert fake_redis.store[f"{SYNC_LOCK_PREFIX}op-1"] == "another-worker-token"

    def test_lock_is_released_after_success(
        self, db, user, sync_service, fake_redis
    ):
        _register(sync_service, db, user, "op-1", "CREATE",
                  payload={"data": {"a": 1}})
        sync_service.process_operation(db, user, "op-1")
        assert fake_redis.store == {}

    def test_lock_is_released_after_failure(
        self, db, user, make_record, sync_service, fake_redis, monkeypatch
    ):
        record = make_record(user, version=1)
        _register(sync_service, db, user, "op-1", "UPDATE", record_id=record.id,
                  base_version=1, payload={"data": {"title": "new"}})
        monkeypatch.setattr(
            sync_service.record_repository, "update",
            lambda *a, **k: (_ for _ in ()).throw(RuntimeError("fail")),
        )

        with pytest.raises(RuntimeError):
            sync_service.process_operation(db, user, "op-1")

        assert fake_redis.store == {}

    def test_lock_is_released_after_a_version_conflict(
        self, db, user, make_record, sync_service, fake_redis
    ):
        record = make_record(user, version=2)
        _register(sync_service, db, user, "op-1", "UPDATE", record_id=record.id,
                  base_version=1, payload={"data": {"title": "new"}})

        with pytest.raises(ConflictException):
            sync_service.process_operation(db, user, "op-1")

        assert fake_redis.store == {}

    def test_processing_continues_when_redis_is_down(
        self, db, user, sync_service, fake_redis
    ):
        fake_redis.fail = True
        _register(sync_service, db, user, "op-1", "CREATE",
                  payload={"data": {"a": 1}})

        op = sync_service.process_operation(db, user, "op-1")

        assert op.status == "SUCCESS"
        assert db.query(Record).count() == 1


# ---------------------------------------------------------------------------
# get_pending_operations
# ---------------------------------------------------------------------------
class TestPendingOperations:
    def test_only_the_users_own_pending_operations_are_returned(
        self, db, user, other_user, sync_service
    ):
        _register(sync_service, db, user, "mine-1", "CREATE", payload={"data": {"a": 1}})
        _register(sync_service, db, user, "mine-2", "CREATE", payload={"data": {"a": 2}})
        _register(sync_service, db, other_user, "theirs-1", "CREATE",
                  payload={"data": {"a": 3}})

        pending = sync_service.get_pending_operations(db, user)

        assert {op.operation_id for op in pending} == {"mine-1", "mine-2"}

    def test_processed_operations_are_no_longer_pending(
        self, db, user, sync_service
    ):
        _register(sync_service, db, user, "op-1", "CREATE", payload={"data": {"a": 1}})
        _register(sync_service, db, user, "op-2", "CREATE", payload={"data": {"a": 2}})
        sync_service.process_operation(db, user, "op-1")

        pending = sync_service.get_pending_operations(db, user)

        assert [op.operation_id for op in pending] == ["op-2"]

    def test_limit_is_respected(self, db, user, sync_service):
        for i in range(5):
            _register(sync_service, db, user, f"op-{i}", "CREATE",
                      payload={"data": {"i": i}})

        assert len(sync_service.get_pending_operations(db, user, limit=3)) == 3
