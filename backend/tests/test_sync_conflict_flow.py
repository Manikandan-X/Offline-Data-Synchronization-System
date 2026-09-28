"""
End-to-end scenarios that cross the SyncService / ConflictService boundary,
mirroring what the frontend does: queue operations, sync them, resolve conflicts.
"""
import pytest

from app.core.exceptions import ConflictException
from app.models.local_sync_operation import LocalSyncOperation
from app.models.record import Record


def _sync(sync_service, db, user, op_id, op_type, record_id=None,
          base_version=0, payload=None):
    sync_service.create_operation(
        db=db, current_user=user, operation_id=op_id, record_id=record_id,
        operation_type=op_type, base_version=base_version, payload=payload,
    )
    return sync_service.process_operation(db, user, op_id)


@pytest.fixture()
def conflicted(db, user, sync_service):
    """
    Device A and device B both start from v1 of the same record; A syncs
    first, so B's stale edit ends up as a pending conflict.
    """
    created = _sync(sync_service, db, user, "create", "CREATE",
                    payload={"data": {"title": "v1"}})
    record_id = created.record_id

    _sync(sync_service, db, user, "edit-a", "UPDATE", record_id=record_id,
          base_version=1, payload={"data": {"title": "from A"}})

    sync_service.create_operation(
        db=db, current_user=user, operation_id="edit-b", record_id=record_id,
        operation_type="UPDATE", base_version=1,
        payload={"data": {"title": "from B"}},
    )
    with pytest.raises(ConflictException):
        sync_service.process_operation(db, user, "edit-b")

    return record_id


def test_conflict_is_listed_as_pending_after_a_stale_sync(
    db, user, conflicted, conflict_service
):
    pending = conflict_service.get_pending_conflicts(db, user)

    assert len(pending) == 1
    assert pending[0].record_id == conflicted
    assert pending[0].client_data == {"title": "from B"}
    assert pending[0].server_data == {"title": "from A"}


def test_client_wins_resolution_applies_the_stale_edit(
    db, user, conflicted, conflict_service
):
    conflict = conflict_service.get_pending_conflicts(db, user)[0]

    conflict_service.resolve_conflict(db, user, conflict.id, "CLIENT_WINS")

    record = db.get(Record, conflicted)
    assert record.data == {"title": "from B"}
    assert record.version == 3  # v1 -> v2 (edit A) -> v3 (resolution)
    assert conflict_service.get_pending_conflicts(db, user) == []


def test_server_wins_resolution_keeps_the_synced_edit(
    db, user, conflicted, conflict_service
):
    conflict = conflict_service.get_pending_conflicts(db, user)[0]

    conflict_service.resolve_conflict(db, user, conflict.id, "SERVER_WINS")

    record = db.get(Record, conflicted)
    assert record.data == {"title": "from A"}
    assert record.version == 3


def test_new_edit_based_on_the_resolved_version_syncs_cleanly(
    db, user, conflicted, conflict_service, sync_service
):
    conflict = conflict_service.get_pending_conflicts(db, user)[0]
    conflict_service.resolve_conflict(db, user, conflict.id, "SERVER_WINS")

    op = _sync(sync_service, db, user, "edit-c", "UPDATE", record_id=conflicted,
               base_version=3, payload={"data": {"title": "after resolution"}})

    assert op.status == "SUCCESS"
    assert db.get(Record, conflicted).version == 4


def test_resolving_does_not_duplicate_or_lose_the_record(
    db, user, conflicted, conflict_service
):
    conflict = conflict_service.get_pending_conflicts(db, user)[0]
    conflict_service.resolve_conflict(db, user, conflict.id, "MANUAL",
                                      resolution_data={"title": "merged"})

    assert db.query(Record).count() == 1
    assert db.get(Record, conflicted).data == {"title": "merged"}


def test_sync_operation_stays_conflict_after_resolution(
    db, user, conflicted, conflict_service, sync_service
):
    """
    Characterization test: resolving a conflict updates the record and the
    Conflict row but does NOT touch the originating LocalSyncOperation, which
    stays CONFLICT and can never be reprocessed. Clients must drop or
    re-create that operation themselves (the frontend removes its queue entry).
    """
    conflict = conflict_service.get_pending_conflicts(db, user)[0]
    conflict_service.resolve_conflict(db, user, conflict.id, "CLIENT_WINS")

    op = db.query(LocalSyncOperation).filter_by(operation_id="edit-b").one()
    assert op.status == "CONFLICT"
    with pytest.raises(ConflictException):
        sync_service.process_operation(db, user, "edit-b")


def test_users_conflicts_are_isolated_from_each_other(
    db, user, other_user, conflicted, conflict_service
):
    assert conflict_service.get_pending_conflicts(db, other_user) == []
