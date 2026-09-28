import json
from typing import Any

from app.core.redis import redis_client


class CacheService:
    """
    Service responsible for Redis cache operations.

    Redis is used only as a performance optimization.
    If Redis is unavailable, cache operations fail safely
    without affecting the main application flow.
    """

    def get(self, key: str) -> Any | None:
        """
        Get a value from Redis.

        Returns None if:
        - The key does not exist.
        - Redis is unavailable.
        - The cached data cannot be decoded.
        """
        try:
            value = redis_client.get(key)

            if value is None:
                return None

            return json.loads(value)

        except Exception:
            return None

    def set(
        self,
        key: str,
        value: Any,
        ttl: int,
    ) -> bool:
        """
        Store a value in Redis with a TTL.

        Returns True when the value is successfully cached.
        Returns False if Redis is unavailable.
        """
        try:
            redis_client.set(
                key,
                json.dumps(value),
                ex=ttl,
            )
            return True

        except Exception:
            return False

    def delete(self, key: str) -> bool:
        """
        Delete a value from Redis.

        Returns True when the operation succeeds.
        Returns False if Redis is unavailable.
        """
        try:
            redis_client.delete(key)
            return True

        except Exception:
            return False


cache_service = CacheService()
