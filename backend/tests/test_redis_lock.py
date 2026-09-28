"""Unit tests for the Redis lock used to prevent concurrent processing."""
import pytest

from app.core.redis import (
    SYNC_LOCK_PREFIX,
    SYNC_LOCK_TIMEOUT_SECONDS,
    RedisLock,
    RedisLockUnavailable,
    try_sync_lock,
)


class TestRedisLock:
    def test_acquire_succeeds_when_free_and_sets_expiry(self, fake_redis):
        lock = RedisLock(fake_redis, "k", timeout=12)

        assert lock.acquire() is True
        assert fake_redis.set_calls[-1] == ("k", lock.token, True, 12)

    def test_second_acquire_on_same_key_fails(self, fake_redis):
        first = RedisLock(fake_redis, "k")
        second = RedisLock(fake_redis, "k")

        assert first.acquire() is True
        assert second.acquire() is False

    def test_release_frees_the_key(self, fake_redis):
        lock = RedisLock(fake_redis, "k")
        lock.acquire()
        lock.release()

        assert "k" not in fake_redis.store
        assert RedisLock(fake_redis, "k").acquire() is True

    def test_release_never_deletes_someone_elses_lock(self, fake_redis):
        mine = RedisLock(fake_redis, "k")
        mine.acquire()
        fake_redis.store["k"] = "token-of-a-different-owner"  # e.g. mine expired

        mine.release()

        assert fake_redis.store["k"] == "token-of-a-different-owner"

    def test_release_without_acquire_is_a_no_op(self, fake_redis):
        fake_redis.store["k"] = "someone-else"
        RedisLock(fake_redis, "k").release()
        assert fake_redis.store["k"] == "someone-else"

    def test_each_lock_has_a_unique_token(self, fake_redis):
        assert RedisLock(fake_redis, "k").token != RedisLock(fake_redis, "k").token


class TestTrySyncLock:
    def test_yields_true_and_holds_the_lock_inside_the_block(self, fake_redis):
        with try_sync_lock("op-1") as acquired:
            assert acquired is True
            assert f"{SYNC_LOCK_PREFIX}op-1" in fake_redis.store

    def test_lock_is_released_on_normal_exit(self, fake_redis):
        with try_sync_lock("op-1"):
            pass
        assert fake_redis.store == {}

    def test_lock_is_released_when_the_body_raises(self, fake_redis):
        with pytest.raises(ValueError):
            with try_sync_lock("op-1"):
                raise ValueError("boom")
        assert fake_redis.store == {}

    def test_already_held_lock_raises_lock_unavailable(self, fake_redis):
        fake_redis.store[f"{SYNC_LOCK_PREFIX}op-1"] = "other"

        with pytest.raises(RedisLockUnavailable):
            with try_sync_lock("op-1"):
                pytest.fail("body must not run when the lock is held")

        assert fake_redis.store[f"{SYNC_LOCK_PREFIX}op-1"] == "other"

    def test_locks_are_per_operation(self, fake_redis):
        with try_sync_lock("op-1"):
            with try_sync_lock("op-2") as acquired:
                assert acquired is True

    def test_redis_outage_degrades_to_no_lock_instead_of_failing(self, fake_redis):
        fake_redis.fail = True
        with try_sync_lock("op-1") as acquired:
            assert acquired is False  # caller proceeds using MySQL only

    def test_default_timeout_is_applied(self, fake_redis):
        with try_sync_lock("op-1"):
            pass
        assert fake_redis.set_calls[-1][3] == SYNC_LOCK_TIMEOUT_SECONDS
