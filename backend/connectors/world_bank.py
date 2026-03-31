"""World Bank API connector for macroeconomic indicators."""

from __future__ import annotations

import asyncio

from connectors.base import BaseConnector


INDICATORS: dict[str, str] = {
    "NY.GDP.MKTP.CD": "gdp_usd",
    "FP.CPI.TOTL.ZG": "inflation",
    "SL.UEM.TOTL.ZS": "unemployment",
}

MACRO_COUNTRIES = ["US", "CN", "DE", "GB", "JP", "IN", "FR", "KR", "NL", "CH"]


class WorldBankConnector(BaseConnector):
    source_name = "world_bank"
    BASE = "https://api.worldbank.org/v2"

    async def fetch_indicator(
        self, country: str, indicator: str, years: int = 10
    ) -> dict | list:
        """Fetch a single indicator for a country over *years* most recent values."""
        url = f"{self.BASE}/country/{country}/indicator/{indicator}"
        return await self._fetch_with_cache(
            url,
            params={"format": "json", "per_page": str(years), "mrv": str(years)},
        )

    async def fetch_all_macro(self) -> dict[str, dict[str, dict | list]]:
        """Batch-fetch GDP, inflation, and unemployment for major economies.

        Returns ``{country: {indicator_name: data, ...}, ...}``.
        """
        results: dict[str, dict[str, dict | list]] = {}

        tasks = []
        task_keys: list[tuple[str, str]] = []
        for country in MACRO_COUNTRIES:
            for code, name in INDICATORS.items():
                tasks.append(self.fetch_indicator(country, code))
                task_keys.append((country, name))

        responses = await asyncio.gather(*tasks, return_exceptions=True)

        for (country, name), resp in zip(task_keys, responses):
            if isinstance(resp, Exception):
                continue
            results.setdefault(country, {})[name] = resp

        return results
