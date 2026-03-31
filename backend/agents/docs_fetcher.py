"""Fetch public API documentation and OpenAPI specs — no API keys needed."""

from __future__ import annotations

import json
import logging
from datetime import datetime
from pathlib import Path

import httpx

logger = logging.getLogger(__name__)

SPECS_DIR = Path(__file__).parent.parent / "docs" / "api_specs"

# Public API documentation sources (no auth required)
PUBLIC_SOURCES = {
    "wikipedia": {
        "docs_url": "https://en.wikipedia.org/api/rest_v1/",
        "openapi_url": "https://en.wikipedia.org/api/rest_v1/?spec",
    },
    "github": {
        "docs_url": "https://api.github.com",
        "openapi_url": None,
    },
    "hn_algolia": {
        "docs_url": "http://hn.algolia.com/api",
        "openapi_url": None,
    },
    "huggingface": {
        "docs_url": "https://huggingface.co/api",
        "openapi_url": None,
    },
    "papers_with_code": {
        "docs_url": "https://paperswithcode.com/api/v1/",
        "openapi_url": None,
    },
    "arxiv": {
        "docs_url": "http://export.arxiv.org/api/query?search_query=all:test&max_results=1",
        "openapi_url": None,
    },
    "npm": {
        "docs_url": "https://registry.npmjs.org/react",
        "openapi_url": None,
    },
    "pypi": {
        "docs_url": "https://pypi.org/pypi/requests/json",
        "openapi_url": None,
    },
    "fred": {
        "docs_url": "https://api.stlouisfed.org/fred/series?series_id=GDP&file_type=json",
        "openapi_url": None,
    },
    "wikidata": {
        "docs_url": "https://www.wikidata.org/w/api.php?action=wbsearchentities&search=Apple&language=en&format=json",
        "openapi_url": None,
    },
    "world_bank": {
        "docs_url": "https://api.worldbank.org/v2/country/US/indicator/NY.GDP.MKTP.CD?format=json&per_page=5",
        "openapi_url": None,
    },
    "sec_edgar": {
        "docs_url": "https://data.sec.gov/submissions/CIK0000320193.json",
        "openapi_url": None,
    },
    "patents_view": {
        "docs_url": "https://api.patentsview.org/patents/query?q={\"patent_number\":\"11000000\"}&f=[\"patent_title\"]",
        "openapi_url": None,
    },
}


async def fetch_all_docs() -> dict:
    """Fetch documentation from all public API sources."""
    SPECS_DIR.mkdir(parents=True, exist_ok=True)
    results = {}
    headers = {"User-Agent": "SovereignOntology/1.0 (docs-fetcher)"}

    async with httpx.AsyncClient(timeout=15, headers=headers, follow_redirects=True) as client:
        for source, urls in PUBLIC_SOURCES.items():
            result = {"source": source, "status": "pending"}

            # Fetch docs endpoint
            try:
                resp = await client.get(urls["docs_url"])
                result["docs_status"] = resp.status_code
                if resp.status_code == 200:
                    content_type = resp.headers.get("content-type", "")
                    if "json" in content_type:
                        doc_data = resp.json()
                    else:
                        doc_data = {"raw": resp.text[:5000]}

                    doc_path = SPECS_DIR / f"{source}.json"
                    doc_path.write_text(json.dumps(doc_data, indent=2, default=str)[:50000])
                    result["docs_path"] = str(doc_path)
                    result["status"] = "ok"
            except Exception as e:
                result["docs_error"] = str(e)
                result["status"] = "error"

            # Fetch OpenAPI spec if available
            if urls.get("openapi_url"):
                try:
                    resp = await client.get(urls["openapi_url"])
                    if resp.status_code == 200:
                        spec_path = SPECS_DIR / f"{source}_openapi.json"
                        spec_path.write_text(json.dumps(resp.json(), indent=2)[:100000])
                        result["openapi_path"] = str(spec_path)
                except Exception as e:
                    result["openapi_error"] = str(e)

            results[source] = result
            logger.info("Docs fetch: %s → %s", source, result["status"])

    # Save summary
    summary = {
        "fetched_at": datetime.utcnow().isoformat(),
        "sources": results,
        "total": len(results),
        "ok": sum(1 for r in results.values() if r["status"] == "ok"),
    }
    (SPECS_DIR / "_summary.json").write_text(json.dumps(summary, indent=2))

    return summary


if __name__ == "__main__":
    import asyncio
    result = asyncio.run(fetch_all_docs())
    print(f"Fetched {result['ok']}/{result['total']} API docs")
