from __future__ import annotations

from connectors.base import BaseConnector


class NpmRegistryConnector(BaseConnector):
    source_name = "npm"
    BASE = "https://registry.npmjs.org"
    DOWNLOADS_BASE = "https://api.npmjs.org/downloads/point/last-month"

    async def fetch_package(self, name: str) -> dict:
        """Fetch package metadata from the npm registry."""
        return await self._fetch_with_cache(f"{self.BASE}/{name}")

    async def fetch_downloads(self, name: str) -> dict:
        """Fetch last-month download counts for a package."""
        return await self._fetch_with_cache(f"{self.DOWNLOADS_BASE}/{name}")
