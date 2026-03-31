"""Base connector with HTTP caching via Redis."""

from __future__ import annotations

import hashlib
import json
from abc import ABC, abstractmethod

import httpx
import redis.asyncio as aioredis


class BaseConnector(ABC):
    source_name: str

    def __init__(self, redis_client: aioredis.Redis, cache_ttl: int = 3600):
        self.redis = redis_client
        self.cache_ttl = cache_ttl

    def _cache_key(self, url: str) -> str:
        url_hash = hashlib.md5(url.encode()).hexdigest()
        return f"raw:{self.source_name}:{url_hash}"

    async def _fetch_with_cache(
        self,
        url: str,
        headers: dict | None = None,
        params: dict | None = None,
    ) -> dict | list:
        """HTTP GET with Redis cache. Returns parsed JSON."""
        cache_key = self._cache_key(url + json.dumps(params or {}, sort_keys=True))

        cached = await self.redis.get(cache_key)
        if cached:
            return json.loads(cached)

        async with httpx.AsyncClient(timeout=30, follow_redirects=True) as client:
            response = await client.get(url, headers=headers, params=params)
            response.raise_for_status()
            data = response.json()

        await self.redis.setex(cache_key, self.cache_ttl, json.dumps(data))
        return data
