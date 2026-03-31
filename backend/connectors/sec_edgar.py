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

    async def fetch_financials(self, cik: str) -> dict:
        """Fetch structured financial data from SEC XBRL. Returns latest annual figures."""
        padded = str(cik).zfill(10)
        data = await self._fetch_with_cache(
            f"{self.BASE}/api/xbrl/companyfacts/CIK{padded}.json",
            headers=self.headers,
        )

        us_gaap = data.get("facts", {}).get("us-gaap", {})
        result: dict = {}

        def _latest_annual(concept: str) -> float | None:
            vals = us_gaap.get(concept, {}).get("units", {})
            entries = vals.get("USD", vals.get("USD/shares", vals.get("shares", [])))
            annual = [v for v in entries if v.get("form") == "10-K"]
            if not annual:
                return None
            annual.sort(key=lambda x: x.get("end", ""), reverse=True)
            return float(annual[0].get("val", 0)) or None

        for concept in ["Revenues", "RevenueFromContractWithCustomerExcludingAssessedTax",
                        "SalesRevenueNet", "RevenueFromContractWithCustomerIncludingAssessedTax"]:
            if val := _latest_annual(concept):
                result["revenue"] = val
                break

        if val := _latest_annual("NetIncomeLoss"):
            result["net_income"] = val
        if val := _latest_annual("Assets"):
            result["total_assets"] = val
        if val := _latest_annual("CashAndCashEquivalentsAtCarryingValue"):
            result["cash"] = val
        if val := _latest_annual("ResearchAndDevelopmentExpense"):
            result["rd_expense"] = val
        if val := _latest_annual("EarningsPerShareBasic"):
            result["eps"] = val

        return result
