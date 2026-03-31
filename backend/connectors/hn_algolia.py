from __future__ import annotations

from connectors.base import BaseConnector


class HNAlgoliaConnector(BaseConnector):
    source_name = "hn_algolia"
    BASE = "https://hn.algolia.com/api/v1"

    async def fetch_search(self, query: str, limit: int = 30) -> dict:
        """Search HN stories via Algolia. Returns hits with title, url, points, num_comments, created_at."""
        return await self._fetch_with_cache(
            f"{self.BASE}/search",
            params={"query": query, "tags": "story", "hitsPerPage": limit},
        )
