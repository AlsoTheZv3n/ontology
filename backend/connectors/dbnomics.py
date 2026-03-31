"""DBnomics connector — 800M time series from FRED, World Bank, IMF, Eurostat, ECB, OECD via one API."""

from __future__ import annotations

from connectors.base import BaseConnector


class DBnomicsConnector(BaseConnector):
    source_name = "dbnomics"
    BASE = "https://db.nomics.world/api/v22"

    async def fetch_series(self, series_id: str) -> dict:
        """Fetch a time series by full ID (e.g. 'FRED/GDP/GDP')."""
        return await self._fetch_with_cache(
            f"{self.BASE}/series/{series_id}",
            cache_ttl=86400,
        )

    async def fetch_search(self, query: str, limit: int = 20) -> dict:
        """Search across all providers."""
        return await self._fetch_with_cache(
            f"{self.BASE}/series",
            params={"q": query, "limit": limit},
        )
