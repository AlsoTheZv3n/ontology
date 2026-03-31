from __future__ import annotations

import asyncio

import feedparser
import httpx

from connectors.base import BaseConnector


class HackerNewsConnector(BaseConnector):
    source_name = "hn_rss"
    BASE = "https://hnrss.org"

    async def fetch_mentions(self, query: str, count: int = 30) -> list[dict]:
        """Fetch HN articles mentioning a query term via RSS."""
        url = f"{self.BASE}/newest?q={query}&count={count}"
        cache_key = self._cache_key(url)

        cached = await self.redis.get(cache_key)
        if cached:
            import json
            return json.loads(cached)

        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.get(url)
            response.raise_for_status()
            text = response.text

        # feedparser is synchronous
        loop = asyncio.get_event_loop()
        feed = await loop.run_in_executor(None, feedparser.parse, text)

        articles = [
            {
                "title": entry.get("title", ""),
                "url": entry.get("link", ""),
                "published": entry.get("published", ""),
                "score": entry.get("hn_points", 0),
                "comments": entry.get("hn_comments", 0),
            }
            for entry in feed.entries
        ]

        import json
        await self.redis.setex(cache_key, self.cache_ttl, json.dumps(articles))
        return articles
