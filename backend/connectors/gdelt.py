"""GDELT Project news intelligence connector."""

from __future__ import annotations

from connectors.base import BaseConnector


class GDELTConnector(BaseConnector):
    source_name = "gdelt"
    BASE = "https://api.gdeltproject.org/api/v2/doc/doc"

    def __init__(self, redis_client, cache_ttl: int = 900):
        super().__init__(redis_client, cache_ttl=cache_ttl)

    async def search_mentions(self, query: str, days: int = 7) -> dict | list:
        """Search recent news mentions via GDELT article list API."""
        return await self._fetch_with_cache(
            self.BASE,
            params={
                "query": query,
                "mode": "artlist",
                "maxrecords": "50",
                "format": "json",
            },
        )
