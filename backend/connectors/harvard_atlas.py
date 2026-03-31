"""Harvard Atlas of Economic Complexity — global trade data."""

from __future__ import annotations

from connectors.base import BaseConnector


class HarvardAtlasConnector(BaseConnector):
    source_name = "harvard_atlas"
    BASE = "https://atlas.cid.harvard.edu/api"

    async def fetch_country_exports(self, country_id: int, year: int = 2022) -> dict:
        """Fetch export data for a country."""
        return await self._fetch_with_cache(
            f"{self.BASE}/data/country/{country_id}/exports/show/{year}/",
            cache_ttl=86400 * 7,
        )

    async def fetch_trade_partners(self, country_id: int) -> dict:
        """Fetch trade partners for a country."""
        return await self._fetch_with_cache(
            f"{self.BASE}/data/country/{country_id}/trade_partners/",
            cache_ttl=86400 * 7,
        )
