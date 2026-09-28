"""Unit tests for ConflictService: conflict creation and resolution strategies."""
import pytest

from app.core.exceptions import BadRequestException, NotFoundException
from app.models.audit_log import AuditLog
from app.models.conflict import Conflict


def _make_conflict(conflict_service, db, user, record, client_version=1,
                   server_version=3, client_data="default", server_data="default"):
    return conflict_service.create_conflict(
        db=db,
        current_user=user,
        record_id=record.id,
        client_version=client_version,
        server_version=server_version,
        client_data={"title": "client"} if client_data == "default" else client_data,
        server_data={"title": "server"} if server_data == "default" else server_data,
    )


def _resolve(conflict_service, db, user, conflict_id, strategy, **kwargs):
    return conflict_service.resolve_conflict(
        db=db,
        current_user=user,
        conflict_id=conflict_id,
        resolution_strategy=strategy,
        **kwargs,
    )


def _audit_actions(db):
    return [a.action for a in db.query(AuditLog).order_by(AuditLog.id)]


@pytest.fixture()
def record(user, make_record):
    """A record sitting at server version 3 with data {"title": "server"}."""
    return make_record(user, data={"title": "server"}, version=3)


# ---------------------------------------------------------------------------
# create_conflict
# ---------------------------------------------------------------------------
class TestCreateConflict:
    def test_new_conflict_starts_pending_and_unresolved(
        self, db, user, record, conflict_service
    ):
        conflict = _make_conflict(conflict_service, db, user, record)

        assert conflict.id is not None
        assert conflict.user_id == user.id
        assert conflict.record_id == record.id
        assert conflict.client_version == 1
        assert conflict.server_version == 3
        assert conflict.client_data == {"title": "client"}
        assert conflict.server_data == {"title": "server"}
        assert conflict.resolution_status == "PENDING"
        assert conflict.resolution_strategy is None
        assert conflict.resolution_notes is None

    def test_creation_writes_an_audit_log(self, db, user, record, conflict_service):
        _make_conflict(conflict_service, db, user, record)
        assert "CONFLICT_CREATED" in _audit_actions(db)

    @pytest.mark.parametrize("client_version, server_version", [(3, 3), (5, 3)])
    def test_client_must_be_strictly_older_than_server(
        self, db, user, record, conflict_service, client_version, server_version
    ):
        with pytest.raises(BadRequestException):
            _make_conflict(conflict_service, db, user, record,
                           client_version=client_version,
                           server_version=server_version)
        assert db.query(Conflict).count() == 0

    def test_negative_client_version_is_rejected(
        self, db, user, record, conflict_service
    ):
        with pytest.raises(BadRequestException):
            _make_conflict(conflict_service, db, user, record,
                           client_version=-1, server_version=3)

    def test_negative_server_version_is_rejected(
        self, db, user, record, conflict_service
    ):
        with pytest.raises(BadRequestException):
            _make_conflict(conflict_service, db, user, record,
                           client_version=-2, server_version=-1)

    def test_version_zero_client_is_valid(self, db, user, record, conflict_service):
        conflict = _make_conflict(conflict_service, db, user, record,
                                  client_version=0, server_version=1)
        assert conflict.client_version == 0


# ---------------------------------------------------------------------------
# resolve_conflict - each strategy
# ---------------------------------------------------------------------------
class TestResolutionStrategies:
    def test_server_wins_keeps_server_data(self, db, user, record, conflict_service):
        conflict = _make_conflict(conflict_service, db, user, record)

        resolved = _resolve(conflict_service, db, user, conflict.id, "SERVER_WINS")

        db.refresh(record)
        assert record.data == {"title": "server"}
        assert resolved.resolution_strategy == "SERVER_WINS"
        assert resolved.resolution_status == "RESOLVED"

    def test_client_wins_overwrites_with_client_data(
        self, db, user, record, conflict_service
    ):
        conflict = _make_conflict(conflict_service, db, user, record)

        resolved = _resolve(conflict_service, db, user, conflict.id, "CLIENT_WINS")

        db.refresh(record)
        assert record.data == {"title": "client"}
        assert resolved.resolution_strategy == "CLIENT_WINS"
        assert resolved.resolution_status == "RESOLVED"

    def test_manual_applies_the_supplied_merge(
        self, db, user, record, conflict_service
    ):
        conflict = _make_conflict(conflict_service, db, user, record)
        merged = {"title": "merged", "extra": True}

        resolved = _resolve(conflict_service, db, user, conflict.id, "MANUAL",
                            resolution_data=merged)

        db.refresh(record)
        assert record.data == merged
        assert resolved.resolution_strategy == "MANUAL"

    def test_manual_requires_resolution_data(
        self, db, user, record, conflict_service
    ):
        conflict = _make_conflict(conflict_service, db, user, record)

        with pytest.raises(BadRequestException):
            _resolve(conflict_service, db, user, conflict.id, "MANUAL")

    def test_last_write_wins_picks_server_when_server_is_newer(
        self, db, user, record, conflict_service
    ):
        conflict = _make_conflict(conflict_service, db, user, record,
                                  client_version=1, server_version=3)

        _resolve(conflict_service, db, user, conflict.id, "LAST_WRITE_WINS")

        db.refresh(record)
        assert record.data == {"title": "server"}

    def test_last_write_wins_picks_client_when_client_version_is_higher(
        self, db, user, record, conflict_service
    ):
        # create_conflict() forbids client >= server, so build this row directly
        conflict = Conflict(
            record_id=record.id, user_id=user.id,
            client_version=5, server_version=3,
            client_data={"title": "client"}, server_data={"title": "server"},
            resolution_status="PENDING",
        )
        db.add(conflict)
        db.commit()

        _resolve(conflict_service, db, user, conflict.id, "LAST_WRITE_WINS")

        db.refresh(record)
        assert record.data == {"title": "client"}

    def test_last_write_wins_prefers_server_on_a_version_tie(
        self, db, user, record, conflict_service
    ):
        conflict = Conflict(
            record_id=record.id, user_id=user.id,
            client_version=3, server_version=3,
            client_data={"title": "client"}, server_data={"title": "server"},
            resolution_status="PENDING",
        )
        db.add(conflict)
        db.commit()

        _resolve(conflict_service, db, user, conflict.id, "LAST_WRITE_WINS")

        db.refresh(record)
        assert record.data == {"title": "server"}

    @pytest.mark.parametrize("strategy", ["SERVER_WINS", "CLIENT_WINS", "MANUAL"])
    def test_every_resolution_moves_the_record_to_the_next_version(
        self, db, user, record, conflict_service, strategy
    ):
        conflict = _make_conflict(conflict_service, db, user, record)
        kwargs = {"resolution_data": {"k": "v"}} if strategy == "MANUAL" else {}

        _resolve(conflict_service, db, user, conflict.id, strategy, **kwargs)

        db.refresh(record)
        assert record.version == 4  # was 3

    def test_strategy_name_is_case_insensitive(
        self, db, user, record, conflict_service
    ):
        conflict = _make_conflict(conflict_service, db, user, record)

        resolved = _resolve(conflict_service, db, user, conflict.id, "client_wins")

        assert resolved.resolution_strategy == "CLIENT_WINS"

    def test_resolution_notes_are_stored(self, db, user, record, conflict_service):
        conflict = _make_conflict(conflict_service, db, user, record)

        resolved = _resolve(conflict_service, db, user, conflict.id, "SERVER_WINS",
                            resolution_notes="Confirmed with the customer")

        assert resolved.resolution_notes == "Confirmed with the customer"

    def test_resolution_writes_an_audit_log(self, db, user, record, conflict_service):
        conflict = _make_conflict(conflict_service, db, user, record)
        _resolve(conflict_service, db, user, conflict.id, "SERVER_WINS")
        assert "CONFLICT_RESOLVED" in _audit_actions(db)


# ---------------------------------------------------------------------------
# resolve_conflict - validation and safety
# ---------------------------------------------------------------------------
class TestResolutionValidation:
    def test_unknown_strategy_is_rejected_and_changes_nothing(
        self, db, user, record, conflict_service
    ):
        conflict = _make_conflict(conflict_service, db, user, record)

        with pytest.raises(BadRequestException):
            _resolve(conflict_service, db, user, conflict.id, "COIN_FLIP")

        db.refresh(record)
        db.refresh(conflict)
        assert record.version == 3
        assert conflict.resolution_status == "PENDING"

    def test_missing_conflict_is_not_found(self, db, user, conflict_service):
        with pytest.raises(NotFoundException):
            _resolve(conflict_service, db, user, 999, "SERVER_WINS")

    def test_cannot_resolve_another_users_conflict(
        self, db, user, other_user, record, conflict_service
    ):
        conflict = _make_conflict(conflict_service, db, user, record)

        with pytest.raises(NotFoundException):
            _resolve(conflict_service, db, other_user, conflict.id, "SERVER_WINS")

        db.refresh(conflict)
        assert conflict.resolution_status == "PENDING"

    def test_a_conflict_can_only_be_resolved_once(
        self, db, user, record, conflict_service
    ):
        conflict = _make_conflict(conflict_service, db, user, record)
        _resolve(conflict_service, db, user, conflict.id, "SERVER_WINS")

        with pytest.raises(BadRequestException):
            _resolve(conflict_service, db, user, conflict.id, "CLIENT_WINS")

        db.refresh(record)
        assert record.version == 4  # bumped once, not twice
        assert record.data == {"title": "server"}  # first resolution stands

    def test_resolving_against_a_deleted_record_is_not_found(
        self, db, user, record, conflict_service
    ):
        conflict = _make_conflict(conflict_service, db, user, record)
        record.is_deleted = True
        db.commit()

        with pytest.raises(NotFoundException):
            _resolve(conflict_service, db, user, conflict.id, "SERVER_WINS")

    @pytest.mark.parametrize("strategy, missing", [
        ("CLIENT_WINS", "client_data"),
        ("SERVER_WINS", "server_data"),
    ])
    def test_choosing_a_side_with_no_data_is_rejected(
        self, db, user, record, conflict_service, strategy, missing
    ):
        kwargs = {missing: None}
        conflict = _make_conflict(conflict_service, db, user, record, **kwargs)

        with pytest.raises(BadRequestException):
            _resolve(conflict_service, db, user, conflict.id, strategy)

        db.refresh(record)
        db.refresh(conflict)
        assert record.version == 3
        assert conflict.resolution_status == "PENDING"


# ---------------------------------------------------------------------------
# Reading conflicts
# ---------------------------------------------------------------------------
class TestReadingConflicts:
    def test_get_conflict_returns_own_conflict(
        self, db, user, record, conflict_service
    ):
        conflict = _make_conflict(conflict_service, db, user, record)
        assert conflict_service.get_conflict(db, user, conflict.id).id == conflict.id

    def test_get_conflict_hides_other_users_conflicts(
        self, db, user, other_user, record, conflict_service
    ):
        conflict = _make_conflict(conflict_service, db, user, record)
        with pytest.raises(NotFoundException):
            conflict_service.get_conflict(db, other_user, conflict.id)

    def test_pending_list_excludes_resolved_and_other_users(
        self, db, user, other_user, make_record, conflict_service
    ):
        rec_a = make_record(user, version=3)
        rec_b = make_record(user, version=3)
        rec_c = make_record(other_user, version=3)

        pending = _make_conflict(conflict_service, db, user, rec_a)
        done = _make_conflict(conflict_service, db, user, rec_b)
        _make_conflict(conflict_service, db, other_user, rec_c)
        _resolve(conflict_service, db, user, done.id, "SERVER_WINS")

        result = conflict_service.get_pending_conflicts(db, user)

        assert [c.id for c in result] == [pending.id]

    def test_all_list_includes_resolved_but_not_other_users(
        self, db, user, other_user, make_record, conflict_service
    ):
        rec_a = make_record(user, version=3)
        rec_b = make_record(other_user, version=3)
        mine = _make_conflict(conflict_service, db, user, rec_a)
        _make_conflict(conflict_service, db, other_user, rec_b)
        _resolve(conflict_service, db, user, mine.id, "SERVER_WINS")

        result = conflict_service.get_conflicts(db, user)

        assert [c.id for c in result] == [mine.id]
