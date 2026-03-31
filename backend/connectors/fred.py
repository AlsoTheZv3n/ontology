from __future__ import annotations

import redis.asyncio as aioredis

from connectors.base import BaseConnector


class FREDConnector(BaseConnector):
    source_name = "fred"
    BASE = "https://api.stlouisfed.org/fred/series/observations"

    def __init__(
        self,
        redis_client: aioredis.Redis,
        api_key: str,
        cache_ttl: int = 3600,
    ):
        super().__init__(redis_client, cache_ttl)
        self.api_key = api_key

    async def fetch_series(self, series_id: str) -> dict:
        """Fetch recent observations for a FRED series (e.g. GDP, UNRATE, FEDFUNDS, CPIAUCSL, DGS10)."""
        return await self._fetch_with_cache(
            self.BASE,
            params={
                "series_id": series_id,
                "api_key": self.api_key,
                "file_type": "json",
                "sort_order": "desc",
                "limit": 30,
            },
        )
