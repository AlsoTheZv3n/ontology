"""Alpha Vantage connector — stock quotes, company overview, earnings."""

from __future__ import annotations

import redis.asyncio as aioredis

from connectors.base import BaseConnector


class AlphaVantageConnector(BaseConnector):
    source_name = "alpha_vantage"
    BASE = "https://www.alphavantage.co/query"

    def __init__(
        self,
        redis_client: aioredis.Redis,
        api_key: str,
        cache_ttl: int = 3600,
    ):
        super().__init__(redis_client, cache_ttl)
        self.api_key = api_key

    async def fetch_overview(self, symbol: str) -> dict:
        """Company overview: market cap, PE, EPS, revenue, sector, etc."""
        return await self._fetch_with_cache(
            self.BASE,
            params={"function": "OVERVIEW", "symbol": symbol, "apikey": self.api_key},
        )

    async def fetch_quote(self, symbol: str) -> dict:
        """Global quote: price, change, volume, etc."""
        return await self._fetch_with_cache(
            self.BASE,
            params={"function": "GLOBAL_QUOTE", "symbol": symbol, "apikey": self.api_key},
        )
