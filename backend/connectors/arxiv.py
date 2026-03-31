from __future__ import annotations

import json
import xml.etree.ElementTree as ET

import httpx

from connectors.base import BaseConnector

# Atom namespace used by arXiv API responses
_ATOM = "{http://www.w3.org/2005/Atom}"


class ArxivConnector(BaseConnector):
    source_name = "arxiv"
    BASE = "https://export.arxiv.org/api/query"

    async def fetch_papers(self, query: str, max_results: int = 20) -> list[dict]:
        """Search arXiv and return parsed paper metadata."""
        url = self.BASE
        params = {
            "search_query": f"all:{query}",
            "max_results": max_results,
        }

        # Build cache key the same way _fetch_with_cache does
        cache_key = self._cache_key(url + json.dumps(params, sort_keys=True))

        cached = await self.redis.get(cache_key)
        if cached:
            return json.loads(cached)

        async with httpx.AsyncClient(timeout=30, follow_redirects=True) as client:
            response = await client.get(url, params=params)
            response.raise_for_status()
            xml_text = response.text

        papers = self._parse_feed(xml_text)

        await self.redis.setex(cache_key, self.cache_ttl, json.dumps(papers))
        return papers

    @staticmethod
    def _parse_feed(xml_text: str) -> list[dict]:
        """Parse Atom XML feed from arXiv into a list of paper dicts."""
        root = ET.fromstring(xml_text)
        papers: list[dict] = []

        for entry in root.findall(f"{_ATOM}entry"):
            # Extract arxiv_id from the <id> tag (URL like http://arxiv.org/abs/XXXX.XXXXX)
            raw_id = entry.findtext(f"{_ATOM}id", "")
            arxiv_id = raw_id.rsplit("/", 1)[-1] if raw_id else ""

            authors = [
                a.findtext(f"{_ATOM}name", "")
                for a in entry.findall(f"{_ATOM}author")
            ]

            # The PDF link has title="pdf"
            pdf_url = ""
            for link in entry.findall(f"{_ATOM}link"):
                if link.attrib.get("title") == "pdf":
                    pdf_url = link.attrib.get("href", "")
                    break

            papers.append(
                {
                    "title": (entry.findtext(f"{_ATOM}title", "") or "").strip(),
                    "authors": authors,
                    "summary": (entry.findtext(f"{_ATOM}summary", "") or "").strip(),
                    "published": entry.findtext(f"{_ATOM}published", ""),
                    "arxiv_id": arxiv_id,
                    "pdf_url": pdf_url,
                }
            )

        return papers
