"""Commodity spot-price connector using gold-api.com (no key required)."""

from __future__ import annotations

import asyncio

from connectors.base import BaseConnector


METALS: dict[str, str] = {
    "XAU": "gold",
    "XAG": "silver",
    "XCU": "copper",
}


class CommoditiesConnector(BaseConnector):
    source_name = "commodities"
    BASE = "https://api.gold-api.com/price"

    def __init__(self, redis_client, cache_ttl: int = 300):
        super().__init__(redis_client, cache_ttl=cache_ttl)

    async def fetch_spot_prices(self) -> dict[str, float | None]:
        """Return a dict of commodity name -> current spot price."""
        tasks = {name: self._fetch_with_cache(f"{self.BASE}/{code}") for code, name in METALS.items()}

        results: dict[str, float | None] = {}
        responses = await asyncio.gather(*tasks.values(), return_exceptions=True)
        for name, resp in zip(tasks.keys(), responses):
            if isinstance(resp, Exception):
                results[name] = None
            else:
                results[name] = resp.get("price") if isinstance(resp, dict) else None

        return results
