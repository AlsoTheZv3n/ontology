"""Map raw API responses to CompanyObject."""

from __future__ import annotations

import re

from schemas.objects import CompanyObject


def _strip_html(text: str | None) -> str | None:
    """Remove HTML tags from a string."""
    if not text:
        return text
    return re.sub(r"<[^>]+>", "", text).strip()


class CompanyMapper:
    def from_wikipedia(self, raw: dict, key: str) -> CompanyObject:
        return CompanyObject(
            key=key,
            properties={
                "name": _strip_html(raw.get("displaytitle")),
                "description": raw.get("extract"),
                "wiki_url": (
                    raw.get("content_urls", {}).get("desktop", {}).get("page")
                ),
            },
            sources={"wikipedia": raw},
        )

    def from_yahoo_finance(self, raw: dict) -> CompanyObject:
        ticker = raw.get("symbol", "").upper()
        city = raw.get("city", "")
        country = raw.get("country", "")
        hq = f"{city}, {country}" if city and country else city or country or None

        return CompanyObject(
            key=ticker.lower(),
            properties={
                "name": raw.get("longName"),
                "ticker": ticker,
                "market_cap": raw.get("marketCap"),
                "employees": raw.get("fullTimeEmployees"),
                "revenue": raw.get("totalRevenue"),
                "pe_ratio": raw.get("trailingPE"),
                "sector": raw.get("sector"),
                "hq": hq,
                "ceo": self._extract_ceo(raw),
            },
            sources={"yahoo_finance": raw},
        )

    def from_github_org(self, raw: dict) -> CompanyObject:
        return CompanyObject(
            key=raw.get("login", "").lower(),
            properties={
                "github_handle": raw.get("login"),
                "github_repos": raw.get("public_repos"),
                "github_followers": raw.get("followers"),
            },
            sources={"github": raw},
        )

    def from_forbes(self, raw: dict) -> CompanyObject:
        name = raw.get("name") or raw.get("company") or ""
        key = name.lower().replace(" ", "-").replace(",", "").replace(".", "")
        return CompanyObject(
            key=key,
            properties={
                "name": name,
                "rank": raw.get("rank"),
                "revenue": raw.get("revenue") or raw.get("revenues_($m)"),
                "employees": raw.get("employees"),
            },
            sources={"forbes": raw},
        )

    def from_sec(self, raw: dict) -> CompanyObject:
        cik = str(raw.get("cik", ""))
        name = raw.get("name") or raw.get("entityName") or ""
        return CompanyObject(
            key=name.lower().replace(" ", "-").replace(",", ""),
            properties={
                "name": name,
                "cik": cik,
                "sic": raw.get("sic"),
                "sic_description": raw.get("sicDescription"),
            },
            sources={"sec_edgar": raw},
        )

    def _extract_ceo(self, raw: dict) -> str | None:
        for officer in raw.get("companyOfficers", []):
            if "CEO" in officer.get("title", ""):
                return officer.get("name")
        return None
