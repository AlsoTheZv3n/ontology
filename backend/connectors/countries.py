"""REST Countries API connector."""

from __future__ import annotations

from connectors.base import BaseConnector

FIELDS = (
    "name,cca2,cca3,capital,region,subregion,"
    "population,area,languages,currencies,borders,latlng,continents"
)


class CountriesConnector(BaseConnector):
    source_name = "countries"
    BASE = "https://restcountries.com/v3.1"

    def __init__(self, redis_client, cache_ttl: int = 604800):
        super().__init__(redis_client, cache_ttl=cache_ttl)

    async def fetch_all(self) -> list:
        """Fetch all countries."""
        return await self._fetch_with_cache(f"{self.BASE}/all")

    async def fetch_country(self, code: str) -> dict | list:
        """Fetch a single country by alpha-2 or alpha-3 code."""
        return await self._fetch_with_cache(f"{self.BASE}/alpha/{code}")
