from __future__ import annotations

from connectors.base import BaseConnector


class PyPIConnector(BaseConnector):
    source_name = "pypi"
    BASE = "https://pypi.org/pypi"

    async def fetch_package(self, name: str) -> dict:
        """Fetch package metadata from PyPI."""
        return await self._fetch_with_cache(f"{self.BASE}/{name}/json")
