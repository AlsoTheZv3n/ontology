"""Finnhub connector — insider transactions, earnings, lobbying, ESG."""

from __future__ import annotations

import redis.asyncio as aioredis

from connectors.base import BaseConnector


class FinnhubConnector(BaseConnector):
    source_name = "finnhub"
    BASE = "https://finnhub.io/api/v1"

    def __init__(self, redis_client: aioredis.Redis, api_key: str, cache_ttl: int = 3600):
        super().__init__(redis_client, cache_ttl)
        self.api_key = api_key

    async def fetch_insider_transactions(self, symbol: str) -> dict:
        return await self._fetch_with_cache(
            f"{self.BASE}/stock/insider-transactions",
            params={"symbol": symbol, "token": self.api_key},
        )

    async def fetch_earnings(self, symbol: str, limit: int = 4) -> list:
        return await self._fetch_with_cache(
            f"{self.BASE}/stock/earnings",
            params={"symbol": symbol, "limit": limit, "token": self.api_key},
        )

    async def fetch_recommendation(self, symbol: str) -> list:
        return await self._fetch_with_cache(
            f"{self.BASE}/stock/recommendation",
            params={"symbol": symbol, "token": self.api_key},
        )

    async def fetch_lobbying(self, symbol: str) -> dict:
        return await self._fetch_with_cache(
            f"{self.BASE}/stock/lobbying",
            params={"symbol": symbol, "from": "2024-01-01", "to": "2026-12-31", "token": self.api_key},
        )
