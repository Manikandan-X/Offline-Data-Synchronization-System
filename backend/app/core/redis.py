from __future__ import annotations

import uuid
from contextlib import contextmanager
from typing import Iterator

from redis import Redis
from redis.exceptions import RedisError

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)

redis_client = Redis.from_url(
    settings.redis_url,
    decode_responses=True,
)

SYNC_LOCK_PREFIX = "sync:operation:"
SYNC_LOCK_TIMEOUT_SECONDS = 30


class RedisLockUnavailable(Exception):
    """
    Raised when Redis is available but the requested lock
    is already held by another process.
    """


class RedisLock:
    """
    Represents a Redis distributed lock.

    The lock has a unique token so that one process cannot
    accidentally release another process's lock.
    """

    def __init__(
        self,
        client: Redis,
        key: str,
        timeout: int = SYNC_LOCK_TIMEOUT_SECONDS,
    ) -> None:
        self.client = client
        self.key = key
        self.timeout = timeout
        self.token = str(uuid.uuid4())
        self.acquired = False

    def acquire(self) -> bool:
        """
        Try to acquire the Redis lock.

        Returns:
            True  -> lock acquired
            False -> lock already exists

        Redis connection errors are allowed to propagate so the
        caller can decide whether to continue without Redis.
        """
        self.acquired = self.client.set(
            self.key,
            self.token,
            nx=True,
            ex=self.timeout,
        )

        return bool(self.acquired)

    def release(self) -> None:
        """
        Release the lock only if this process owns it.

        Uses a small Lua script so checking the token and deleting
        the key happen atomically.
        """
        if not self.acquired:
            return

        release_script = """
        if redis.call("get", KEYS[1]) == ARGV[1] then
            return redis.call("del", KEYS[1])
        else
            return 0
        end
        """

        try:
            self.client.eval(
                release_script,
                1,
                self.key,
                self.token,
            )
        finally:
            self.acquired = False


@contextmanager
def try_sync_lock(
    operation_id: str,
) -> Iterator[bool]:
    """
    Attempt to acquire a Redis lock for a sync operation.

    This function deliberately treats Redis as optional.

    Redis available + lock acquired:
        yields True

    Redis available + lock already held:
        raises RedisLockUnavailable

    Redis unavailable:
        logs the failure and yields False

    In the Redis failure case, the caller continues using MySQL.
    """

    lock = RedisLock(
        client=redis_client,
        key=f"{SYNC_LOCK_PREFIX}{operation_id}",
    )

    try:
        try:
            acquired = lock.acquire()

        except RedisError as exc:
            logger.warning(
                "Redis unavailable while acquiring sync lock: "
                "operation_id=%s error=%s. "
                "Continuing with MySQL processing.",
                operation_id,
                str(exc),
            )

            yield False
            return

        if not acquired:
            raise RedisLockUnavailable(
                f"Sync operation '{operation_id}' is already being processed"
            )

        logger.debug(
            "Redis sync lock acquired: operation_id=%s",
            operation_id,
        )

        yield True

    finally:
        if lock.acquired:
            try:
                lock.release()

                logger.debug(
                    "Redis sync lock released: operation_id=%s",
                    operation_id,
                )

            except RedisError as exc:
                logger.warning(
                    "Failed to release Redis sync lock: "
                    "operation_id=%s error=%s",
                    operation_id,
                    str(exc),
                )