"""Wikidata SPARQL connector — structured company and person data."""

from __future__ import annotations

import json
import logging
import re
from contextlib import suppress
from typing import Any

import httpx

from connectors.base import BaseConnector

logger = logging.getLogger(__name__)

ENDPOINT = "https://query.wikidata.org/sparql"
HEADERS = {
    "User-Agent": "SovereignOntology/1.0 (https://github.com/AlsoTheZv3n/ontology)",
    "Accept": "application/sparql-results+json",
}

COMPANY_QIDS: dict[str, str] = {
    "apple": "Q312", "microsoft": "Q2283", "google": "Q95", "meta": "Q380",
    "amazon": "Q3884", "nvidia": "Q182477", "tesla": "Q478214",
    "netflix": "Q907311", "salesforce": "Q286736", "adobe": "Q154956",
    "ibm": "Q37156", "oracle": "Q190735", "intel": "Q248", "cisco": "Q182963",
    "qualcomm": "Q1829168", "amd": "Q428940", "broadcom": "Q559477",
    "paypal": "Q1863", "uber": "Q22247606", "airbnb": "Q2916552",
    "shopify": "Q14845079", "crowdstrike": "Q28547425", "palantir": "Q3350979",
    "snowflake": "Q79840", "elastic": "Q28547427", "atlassian": "Q3611694",
    "gitlab": "Q16639197", "mongodb": "Q1165594", "twilio": "Q28547415",
    "zoom": "Q56258888", "cloudflare": "Q28547416", "stripe": "Q22109508",
    "spotify": "Q390321", "databricks": "Q59988302", "anthropic": "Q113215742",
    "openai": "Q21708202", "hugging face": "Q107104961", "sap": "Q44120",
    "block": "Q3737458", "doordash": "Q56257960", "palo alto networks": "Q3738746",
    "fortinet": "Q1415948", "plaid": "Q64067103", "vercel": "Q116741367",
    "supabase": "Q107172671", "jetbrains": "Q1855078",
}


class WikidataConnector(BaseConnector):
    source_name = "wikidata"

    async def _sparql(self, query: str, cache_ttl: int = 86400) -> list[dict[str, Any]]:
        """Execute a SPARQL query and return parsed bindings."""
        cache_key = self._cache_key(f"sparql:{query[:200]}")
        cached = await self.redis.get(cache_key)
        if cached:
            return json.loads(cached)

        async with httpx.AsyncClient(
            timeout=30, headers=HEADERS, follow_redirects=True,
        ) as client:
            resp = await client.get(ENDPOINT, params={"query": query, "format": "json"})
            resp.raise_for_status()
            data = resp.json()

        results = data.get("results", {}).get("bindings", [])
        await self.redis.setex(cache_key, cache_ttl, json.dumps(results))
        return results

    @staticmethod
    def _val(binding: dict, key: str) -> str | None:
        entry = binding.get(key)
        if not entry:
            return None
        return entry.get("value", "").strip() or None

    async def fetch_all_companies(self) -> dict[str, dict[str, Any]]:
        """Batch fetch all known companies in one SPARQL query."""
        values = " ".join(f'(wd:{qid} "{key}")' for key, qid in COMPANY_QIDS.items())

        query = f"""
        SELECT ?companyKey ?ceoLabel ?founderLabel ?founded ?hqLabel ?employees WHERE {{
          VALUES (?company ?companyKey) {{ {values} }}
          OPTIONAL {{ ?company wdt:P169 ?ceo. }}
          OPTIONAL {{ ?company wdt:P112 ?founder. }}
          OPTIONAL {{ ?company wdt:P571 ?founded. }}
          OPTIONAL {{ ?company wdt:P159 ?hq. }}
          OPTIONAL {{ ?company wdt:P1128 ?employees. }}
          SERVICE wikibase:label {{ bd:serviceParam wikibase:language "en". }}
        }}
        """

        try:
            bindings = await self._sparql(query, cache_ttl=3600)
        except Exception as e:
            logger.error("Wikidata batch query failed: %s", e)
            return {}

        results: dict[str, dict] = {}
        for b in bindings:
            key = self._val(b, "companyKey")
            if not key:
                continue
            if key not in results:
                results[key] = {}
            r = results[key]
            if ceo := self._val(b, "ceoLabel"):
                r["ceo"] = ceo
            if founder := self._val(b, "founderLabel"):
                r.setdefault("founders", [])
                if founder not in r["founders"]:
                    r["founders"].append(founder)
            if founded := self._val(b, "founded"):
                if m := re.match(r"(\d{4})", founded):
                    r["founded"] = int(m.group(1))
            if hq := self._val(b, "hqLabel"):
                r["hq"] = hq
            if employees := self._val(b, "employees"):
                with suppress(ValueError):
                    r["employees"] = int(employees)

        logger.info("Wikidata: fetched data for %d companies", len(results))
        return results
