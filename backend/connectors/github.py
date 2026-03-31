from __future__ import annotations

from connectors.base import BaseConnector
import redis.asyncio as aioredis


class GitHubConnector(BaseConnector):
    source_name = "github"
    BASE = "https://api.github.com"

    def __init__(
        self,
        redis_client: aioredis.Redis,
        token: str = "",
        cache_ttl: int = 3600,
    ):
        super().__init__(redis_client, cache_ttl)
        self.headers: dict[str, str] = {}
        if token:
            self.headers["Authorization"] = f"Bearer {token}"

    async def fetch_org(self, org: str) -> dict:
        return await self._fetch_with_cache(
            f"{self.BASE}/orgs/{org}", headers=self.headers
        )

    async def fetch_repos(self, org: str, per_page: int = 100) -> list[dict]:
        return await self._fetch_with_cache(
            f"{self.BASE}/orgs/{org}/repos",
            headers=self.headers,
            params={"per_page": per_page, "sort": "stars"},
        )
