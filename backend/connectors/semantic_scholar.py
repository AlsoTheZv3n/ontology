"""Semantic Scholar academic paper API connector."""

from __future__ import annotations

from connectors.base import BaseConnector

PAPER_FIELDS = "title,authors,year,citationCount,abstract"
AUTHOR_FIELDS = "name,affiliations,paperCount,citationCount,hIndex"


class SemanticScholarConnector(BaseConnector):
    source_name = "semantic_scholar"
    BASE = "https://api.semanticscholar.org/graph/v1"

    async def search_papers(self, query: str, limit: int = 20) -> dict | list:
        """Search papers by keyword."""
        return await self._fetch_with_cache(
            f"{self.BASE}/paper/search",
            params={"query": query, "limit": str(limit), "fields": PAPER_FIELDS},
        )

    async def fetch_author(self, author_id: str) -> dict | list:
        """Fetch author profile by Semantic Scholar author ID."""
        return await self._fetch_with_cache(
            f"{self.BASE}/author/{author_id}",
            params={"fields": AUTHOR_FIELDS},
        )
