from __future__ import annotations

import json
import httpx

from connectors.base import BaseConnector


class PapersWithCodeConnector(BaseConnector):
    source_name = "papers_with_code"
    BASE = "https://paperswithcode.com/api/v1"

    async def fetch_papers(self, query: str, limit: int = 20) -> dict:
        """Search papers on Papers with Code."""
        url = f"{self.BASE}/search/"
        params = {"q": query, "page": 1}
        cache_key = self._cache_key(url + json.dumps(params, sort_keys=True))

        cached = await self.redis.get(cache_key)
        if cached:
            return json.loads(cached)

        async with httpx.AsyncClient(
            timeout=15,
            follow_redirects=True,
            headers={"User-Agent": "SovereignOntology/1.0"},
        ) as client:
            resp = await client.get(url, params=params)
            if resp.status_code != 200 or not resp.text.strip():
                return {"results": [], "count": 0}
            try:
                data = resp.json()
            except Exception:
                return {"results": [], "count": 0}

        await self.redis.setex(cache_key, self.cache_ttl, json.dumps(data))
        return data
