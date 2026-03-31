"""Redis-based response cache for API endpoints."""

from __future__ import annotations

import json

import redis.asyncio as aioredis


class ResponseCache:
    def __init__(self, redis_client: aioredis.Redis, default_ttl: int = 300):
        self.redis = redis_client
        self.default_ttl = default_ttl

    async def get(self, key: str) -> dict | list | None:
        raw = await self.redis.get(f"api:{key}")
        if raw:
            return json.loads(raw)
        return None

    async def set(self, key: str, value: dict | list, ttl: int | None = None) -> None:
        await self.redis.setex(
            f"api:{key}",
            ttl or self.default_ttl,
            json.dumps(value, default=str),
        )

    async def invalidate(self, pattern: str) -> int:
        """Delete all keys matching a pattern. Returns count deleted."""
        keys = []
        async for key in self.redis.scan_iter(f"api:{pattern}"):
            keys.append(key)
        if keys:
            return await self.redis.delete(*keys)
        return 0
