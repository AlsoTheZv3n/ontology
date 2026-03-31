from __future__ import annotations

import redis.asyncio as aioredis

from connectors.base import BaseConnector


class EIAConnector(BaseConnector):
    source_name = "eia"
    BASE = "https://api.eia.gov/v2/seriesid"

    def __init__(
        self,
        redis_client: aioredis.Redis,
        api_key: str,
        cache_ttl: int = 3600,
    ):
        super().__init__(redis_client, cache_ttl)
        self.api_key = api_key

    async def fetch_series(self, series_id: str) -> dict:
        """Fetch energy data series from the EIA API."""
        return await self._fetch_with_cache(
            f"{self.BASE}/{series_id}",
            params={"api_key": self.api_key},
        )
