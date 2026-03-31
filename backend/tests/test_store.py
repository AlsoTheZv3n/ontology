"""Tests for the store layer (cache only — writer/reader need real Postgres)."""

import json

import pytest
import fakeredis.aioredis

from store.cache import ResponseCache


class TestResponseCache:
    @pytest.fixture
    def cache(self):
        redis = fakeredis.aioredis.FakeRedis()
        return ResponseCache(redis, default_ttl=60)

    async def test_get_miss(self, cache):
        result = await cache.get("nonexistent")
        assert result is None

    async def test_set_and_get(self, cache):
        data = {"items": [1, 2, 3], "total": 3}
        await cache.set("test-key", data)

        result = await cache.get("test-key")
        assert result == data

    async def test_custom_ttl(self, cache):
        await cache.set("short-lived", {"ok": True}, ttl=10)
        result = await cache.get("short-lived")
        assert result == {"ok": True}

    async def test_invalidate(self, cache):
        await cache.set("objects:list", {"a": 1})
        await cache.set("objects:detail", {"b": 2})
        await cache.set("graph:root", {"c": 3})

        deleted = await cache.invalidate("objects:*")
        assert deleted == 2

        assert await cache.get("objects:list") is None
        assert await cache.get("graph:root") == {"c": 3}
