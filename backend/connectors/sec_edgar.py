from __future__ import annotations

from connectors.base import BaseConnector
import redis.asyncio as aioredis


class SECEdgarConnector(BaseConnector):
    source_name = "sec_edgar"
    BASE = "https://data.sec.gov"

    def __init__(
        self,
        redis_client: aioredis.Redis,
        user_agent: str = "Ontology ontology@example.com",
        cache_ttl: int = 3600,
    ):
        super().__init__(redis_client, cache_ttl)
        self.headers = {"User-Agent": user_agent}

    async def fetch_submissions(self, cik: str) -> dict:
        """Fetch company submissions (filings list)."""
        return await self._fetch_with_cache(
            f"{self.BASE}/submissions/CIK{cik}.json",
            headers=self.headers,
        )

    async def fetch_company_facts(self, cik: str) -> dict:
        """Fetch XBRL financial facts."""
        return await self._fetch_with_cache(
            f"{self.BASE}/api/xbrl/companyfacts/CIK{cik}.json",
            headers=self.headers,
        )
