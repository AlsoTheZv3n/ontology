from __future__ import annotations

import json

from connectors.base import BaseConnector


class PatentsViewConnector(BaseConnector):
    source_name = "patents"
    BASE = "https://api.patentsview.org/patents/query"

    async def fetch_by_company(self, company_name: str, per_page: int = 100) -> dict:
        """Fetch patents filed by a company (uses _contains for fuzzy match)."""
        params = {
            "q": json.dumps({"_contains": {"assignee_organization": company_name}}),
            "f": json.dumps([
                "patent_title",
                "patent_date",
                "patent_number",
                "inventor_first_name",
                "inventor_last_name",
                "assignee_organization",
            ]),
            "o": json.dumps({"per_page": per_page}),
        }
        return await self._fetch_with_cache(self.BASE, params=params)
