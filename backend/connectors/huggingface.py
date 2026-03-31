from __future__ import annotations

from connectors.base import BaseConnector


class HuggingFaceConnector(BaseConnector):
    source_name = "huggingface"
    BASE = "https://huggingface.co/api"

    async def fetch_models(self, org: str) -> list[dict]:
        """Fetch top models for an organization sorted by downloads."""
        return await self._fetch_with_cache(
            f"{self.BASE}/models",
            params={"author": org, "sort": "downloads", "limit": 20},
        )

    async def fetch_org(self, org: str) -> dict:
        """Fetch organization profile info."""
        return await self._fetch_with_cache(
            f"{self.BASE}/organizations/{org}",
        )
