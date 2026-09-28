"""
Shared fixtures for the synchronization / conflict-resolution unit tests.

Design notes
------------
* No MySQL and no Redis are needed. Each test gets a fresh in-memory SQLite
  database and a fake Redis client, so the suite runs anywhere in seconds.
* Environment variables are set *before* any ``app`` import because
  ``app.core.config.Settings`` reads them at import time.
* Services are exercised through their public methods with a real SQLAlchemy
  session, so transactions, rollbacks and constraints behave like production.
"""
import os

# --- must run before importing anything from ``app`` -----------------------
_TEST_ENV = {
    "APP_NAME": "SyncGrid Test",
    "APP_VERSION": "0.0.0",
    "DEBUG": "false",
    "MYSQL_HOST": "localhost",
    "MYSQL_PORT": "3306",
    "MYSQL_DATABASE": "test",
    "MYSQL_USER": "test",
    "MYSQL_PASSWORD": "test",
    "MYSQL_ROOT_PASSWORD": "test",
    "REDIS_HOST": "localhost",
    "REDIS_PORT": "6379",
    "REDIS_DB": "0",
    "REDIS_URL": "redis://localhost:6379/0",
    "REDIS_CACHE_TTL": "60",
    "JWT_SECRET_KEY": "test-secret",
    "JWT_ALGORITHM": "HS256",
    "JWT_ACCESS_TOKEN_EXPIRE_MINUTES": "60",
    "DATABASE_URL": "sqlite://",
}
for _key, _value in _TEST_ENV.items():
    os.environ.setdefault(_key, _value)
# ---------------------------------------------------------------------------

import pytest
from redis.exceptions import RedisError
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

import app.db.base  # noqa: F401  (registers every model on Base.metadata)
from app.db.base_class import Base
from app.models.record import Record
from app.models.role import Role
from app.models.user import User
from app.services.conflict_service import ConflictService
from app.services.sync_service import SyncService


# ---------------------------------------------------------------------------
# Database
# ---------------------------------------------------------------------------
@pytest.fixture()
def db():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    session = sessionmaker(bind=engine, autoflush=False, autocommit=False)()

    session.add_all(
        [
            Role(name="Admin", description="System administrator"),
            Role(name="User", description="Regular application user"),
        ]
    )
    session.commit()

    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(engine)
        engine.dispose()


def _make_user(db, email: str, first_name: str = "Test") -> User:
    user_role = db.query(Role).filter(Role.name == "User").one()
    user = User(
        first_name=first_name,
        last_name="User",
        email=email,
        hashed_password="not-a-real-hash",
        is_active=True,
        role_id=user_role.id,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture()
def user(db) -> User:
    return _make_user(db, "alice@example.com", "Alice")


@pytest.fixture()
def other_user(db) -> User:
    return _make_user(db, "bob@example.com", "Bob")


@pytest.fixture()
def make_record(db):
    """Factory: create a record directly in the DB (bypassing the sync engine)."""

    def _make(owner: User, data: dict | None = None, version: int = 1,
              is_deleted: bool = False) -> Record:
        record = Record(
            owner_id=owner.id,
            data=data if data is not None else {"title": "original"},
            version=version,
            is_deleted=is_deleted,
        )
        db.add(record)
        db.commit()
        db.refresh(record)
        return record

    return _make


# ---------------------------------------------------------------------------
# Services
# ---------------------------------------------------------------------------
@pytest.fixture()
def sync_service() -> SyncService:
    return SyncService()


@pytest.fixture()
def conflict_service() -> ConflictService:
    return ConflictService()


# ---------------------------------------------------------------------------
# Fake Redis (autouse -> no test ever touches a real Redis server)
# ---------------------------------------------------------------------------
class FakeRedis:
    """
    Minimal stand-in for the redis client used by ``app.core.redis``.

    Supports exactly what RedisLock needs: ``set(nx, ex)`` and the
    token-checked ``eval`` release script. Set ``fail = True`` to simulate
    an outage (every call raises RedisError).
    """

    def __init__(self) -> None:
        self.store: dict[str, str] = {}
        self.fail = False
        self.set_calls: list[tuple] = []

    def set(self, key, value, nx=False, ex=None):
        if self.fail:
            raise RedisError("simulated redis outage")
        self.set_calls.append((key, value, nx, ex))
        if nx and key in self.store:
            return None
        self.store[key] = value
        return True

    def eval(self, script, numkeys, key, token):
        if self.fail:
            raise RedisError("simulated redis outage")
        if self.store.get(key) == token:
            del self.store[key]
            return 1
        return 0


@pytest.fixture(autouse=True)
def fake_redis(monkeypatch) -> FakeRedis:
    client = FakeRedis()
    monkeypatch.setattr("app.core.redis.redis_client", client)
    return client
