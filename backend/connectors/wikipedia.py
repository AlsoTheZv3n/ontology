from connectors.base import BaseConnector


class WikipediaConnector(BaseConnector):
    source_name = "wikipedia"
    BASE = "https://en.wikipedia.org/api/rest_v1"

    async def fetch_company(self, slug: str) -> dict:
        return await self._fetch_with_cache(
            f"{self.BASE}/page/summary/{slug}",
            headers={"User-Agent": "SovereignOntology/1.0 (ontology@example.com)"},
        )
