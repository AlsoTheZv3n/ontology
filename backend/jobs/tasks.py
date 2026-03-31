"""Sync tasks — each function fetches from one source and upserts into the ontology."""

from __future__ import annotations

import asyncio
import logging

import asyncpg
import redis.asyncio as aioredis

from connectors.wikipedia import WikipediaConnector
from connectors.github import GitHubConnector
from connectors.yahoo_finance import YahooFinanceConnector
from connectors.sec_edgar import SECEdgarConnector
from connectors.hn_rss import HackerNewsConnector
from connectors.forbes_csv import ForbesConnector
from connectors.patents import PatentsViewConnector
from connectors.huggingface import HuggingFaceConnector
from connectors.hn_algolia import HNAlgoliaConnector
from transform.mappers.company import CompanyMapper
from transform.mappers.article import ArticleMapper
from transform.mappers.repo import RepoMapper
from transform.mappers.event import EventMapper
from transform.derived import DerivedPropertyEngine
from store.writer import OntologyWriter
from schemas.seed import COMPANIES

logger = logging.getLogger(__name__)


def _canonical(company: dict) -> str:
    """Canonical key for a company from seed data."""
    return company["name"].lower()


async def sync_wikipedia(ctx: dict) -> int:
    """Sync Wikipedia data for all seeded companies."""
    pool: asyncpg.Pool = ctx["pool"]
    redis_client: aioredis.Redis = ctx["redis"]
    conn = WikipediaConnector(redis_client)
    mapper = CompanyMapper()
    writer = OntologyWriter(pool)
    count = 0

    for company in COMPANIES:
        slug = company.get("wiki")
        if not slug:
            continue
        try:
            raw = await conn.fetch_company(slug)
            await writer.save_raw_snapshot("wikipedia", slug, raw)
            obj = mapper.from_wikipedia(raw, _canonical(company))
            await writer.upsert(obj)
            count += 1
        except Exception:
            logger.exception("Wikipedia sync failed for %s", slug)

    return count


async def sync_github(ctx: dict) -> int:
    """Sync GitHub org + repos for all seeded companies."""
    pool: asyncpg.Pool = ctx["pool"]
    redis_client: aioredis.Redis = ctx["redis"]
    token = ctx.get("github_token", "")
    conn = GitHubConnector(redis_client, token=token)
    company_mapper = CompanyMapper()
    repo_mapper = RepoMapper()
    writer = OntologyWriter(pool)
    count = 0

    for company in COMPANIES:
        org = company.get("github")
        if not org:
            continue
        try:
            org_raw = await conn.fetch_org(org)
            await writer.save_raw_snapshot("github", org, org_raw)
            obj = company_mapper.from_github_org(org_raw)
            obj.key = _canonical(company)
            company_id = await writer.upsert(obj)

            repos = await conn.fetch_repos(org)
            for repo in repos[:20]:
                repo_obj = repo_mapper.from_github(repo)
                repo_id = await writer.upsert(repo_obj)
                await writer.upsert_link("owns_repo", company_id, repo_id)

            count += 1
        except Exception:
            logger.exception("GitHub sync failed for %s", org)

    return count


async def sync_yahoo_finance(ctx: dict) -> int:
    """Sync market data via Alpha Vantage (replaces broken Yahoo Finance).

    Uses OVERVIEW endpoint for fundamentals: market_cap, pe_ratio, eps,
    revenue, employees, sector, etc.
    Falls back to Yahoo Finance if AV key not set.
    """
    from connectors.alpha_vantage import AlphaVantageConnector
    from config import settings as _s

    pool: asyncpg.Pool = ctx["pool"]
    redis_client: aioredis.Redis = ctx["redis"]
    writer = OntologyWriter(pool)
    count = 0

    if _s.alpha_vantage_key:
        av = AlphaVantageConnector(redis_client, api_key=_s.alpha_vantage_key)
        for company in COMPANIES:
            ticker = company.get("ticker")
            if not ticker:
                continue
            try:
                raw = await av.fetch_overview(ticker)
                if not raw or "Symbol" not in raw:
                    continue
                await writer.save_raw_snapshot("alpha_vantage", ticker, raw)
                from schemas.objects import CompanyObject
                obj = CompanyObject(
                    key=_canonical(company),
                    properties={
                        "name": raw.get("Name"),
                        "ticker": raw.get("Symbol"),
                        "market_cap": float(raw["MarketCapitalization"]) if raw.get("MarketCapitalization") else None,
                        "pe_ratio": float(raw["PERatio"]) if raw.get("PERatio") and raw["PERatio"] != "None" else None,
                        "eps": float(raw["EPS"]) if raw.get("EPS") and raw["EPS"] != "None" else None,
                        "revenue": float(raw["RevenueTTM"]) if raw.get("RevenueTTM") else None,
                        "employees": int(raw["FullTimeEmployees"]) if raw.get("FullTimeEmployees") else None,
                        "sector": raw.get("Sector"),
                        "industry": raw.get("Industry"),
                        "hq": raw.get("Address"),
                        "dividend_yield": raw.get("DividendYield"),
                        "52w_high": float(raw["52WeekHigh"]) if raw.get("52WeekHigh") else None,
                        "52w_low": float(raw["52WeekLow"]) if raw.get("52WeekLow") else None,
                        "analyst_target": float(raw["AnalystTargetPrice"]) if raw.get("AnalystTargetPrice") else None,
                    },
                    sources={"alpha_vantage": raw},
                )
                await writer.upsert(obj)
                count += 1
                # Alpha Vantage free tier: 25 req/day, so pace requests
                import asyncio
                await asyncio.sleep(1)
            except Exception:
                logger.exception("Alpha Vantage sync failed for %s", ticker)
    else:
        # Fallback to Yahoo Finance
        conn = YahooFinanceConnector(redis_client)
        mapper = CompanyMapper()
        for company in COMPANIES:
            ticker = company.get("ticker")
            if not ticker:
                continue
            try:
                raw = await conn.fetch_ticker(ticker)
                await writer.save_raw_snapshot("yahoo_finance", ticker, raw)
                obj = mapper.from_yahoo_finance(raw)
                obj.key = _canonical(company)
                await writer.upsert(obj)
                count += 1
            except Exception:
                logger.exception("Yahoo Finance sync failed for %s", ticker)

    return count


async def sync_hn(ctx: dict) -> int:
    """Sync Hacker News mentions for all seeded companies."""
    pool: asyncpg.Pool = ctx["pool"]
    redis_client: aioredis.Redis = ctx["redis"]
    conn = HackerNewsConnector(redis_client)
    mapper = ArticleMapper()
    writer = OntologyWriter(pool)
    count = 0

    for company in COMPANIES:
        name = company["name"]
        try:
            articles = await conn.fetch_mentions(name, count=20)
            for article in articles:
                obj = mapper.from_hn(article)
                article_id = await writer.upsert(obj)

                company_id = await writer.get_id("company", name.lower())
                if company_id:
                    await writer.upsert_link("mentions", article_id, company_id)
                count += 1
        except Exception:
            logger.exception("HN sync failed for %s", name)

    return count


async def sync_sec(ctx: dict) -> int:
    """Sync SEC EDGAR submissions for companies with CIK."""
    pool: asyncpg.Pool = ctx["pool"]
    redis_client: aioredis.Redis = ctx["redis"]
    user_agent = ctx.get("sec_user_agent", "Ontology ontology@example.com")
    conn = SECEdgarConnector(redis_client, user_agent=user_agent)
    mapper = CompanyMapper()
    event_mapper = EventMapper()
    writer = OntologyWriter(pool)
    count = 0

    for company in COMPANIES:
        cik = company.get("cik")
        if not cik:
            continue
        try:
            raw = await conn.fetch_submissions(cik)
            await writer.save_raw_snapshot("sec_edgar", cik, raw)
            obj = mapper.from_sec(raw)
            obj.key = _canonical(company)
            company_id = await writer.upsert(obj)

            filings = raw.get("filings", {}).get("recent", {})
            forms = filings.get("form", [])
            dates = filings.get("filingDate", [])
            accessions = filings.get("accessionNumber", [])
            descriptions = filings.get("primaryDocDescription", [])

            for i in range(min(10, len(forms))):
                filing_raw = {
                    "form": forms[i] if i < len(forms) else "",
                    "filingDate": dates[i] if i < len(dates) else "",
                    "accessionNumber": accessions[i] if i < len(accessions) else "",
                    "primaryDocDescription": descriptions[i] if i < len(descriptions) else "",
                }
                event_obj = event_mapper.from_sec_filing(filing_raw, company["name"].lower())
                event_id = await writer.upsert(event_obj)
                await writer.upsert_link("filed", company_id, event_id)

            count += 1
        except Exception:
            logger.exception("SEC sync failed for %s", cik)

    return count


async def sync_patents(ctx: dict) -> int:
    """Sync patents from PatentsView."""
    pool: asyncpg.Pool = ctx["pool"]
    redis_client: aioredis.Redis = ctx["redis"]
    conn = PatentsViewConnector(redis_client)
    event_mapper = EventMapper()
    writer = OntologyWriter(pool)
    count = 0

    for company in COMPANIES:
        name = company["name"]
        try:
            raw = await conn.fetch_by_company(name)
            patents = raw.get("patents") or []
            for patent in patents[:20]:
                obj = event_mapper.from_patent(patent, name.lower())
                event_id = await writer.upsert(obj)

                company_id = await writer.get_id("company", name.lower())
                if company_id:
                    await writer.upsert_link("filed", company_id, event_id)
                count += 1
        except Exception:
            logger.exception("Patents sync failed for %s", name)

    return count


HF_ORG_MAP: dict[str, list[str]] = {
    "google": ["google", "google-deepmind"],
    "meta": ["meta-llama", "facebook"],
    "microsoft": ["microsoft"],
    "anthropic": ["anthropic"],
    "openai": ["openai", "openai-community"],
    "nvidia": ["nvidia"],
    "mistral": ["mistralai"],
    "apple": ["apple"],
    "amazon": ["amazon"],
    "ibm": ["ibm"],
    "salesforce": ["salesforce-ai", "Salesforce"],
    "databricks": ["databricks"],
    "hugging face": ["huggingface"],
}


async def sync_huggingface(ctx: dict) -> int:
    """Sync HuggingFace models for companies (uses expanded org map)."""
    pool: asyncpg.Pool = ctx["pool"]
    redis_client: aioredis.Redis = ctx["redis"]
    conn = HuggingFaceConnector(redis_client)
    writer = OntologyWriter(pool)
    count = 0

    for company in COMPANIES:
        canonical = _canonical(company)
        orgs = HF_ORG_MAP.get(canonical)
        if not orgs:
            org = company.get("github")
            orgs = [org] if org else []
        if not orgs:
            continue
        try:
            all_models: list = []
            for org in orgs:
                models = await conn.fetch_models(org)
                if isinstance(models, list):
                    all_models.extend(models)
            if not all_models:
                continue
            total_downloads = sum(m.get("downloads", 0) for m in all_models)
            total_likes = sum(m.get("likes", 0) for m in all_models)
            from schemas.objects import CompanyObject
            obj = CompanyObject(
                key=canonical,
                properties={
                    "hf_model_count": len(all_models),
                    "hf_total_downloads": total_downloads,
                    "hf_total_likes": total_likes,
                    "hf_top_model": all_models[0].get("modelId") if all_models else None,
                },
                sources={"huggingface": {"model_count": len(all_models), "orgs": orgs}},
            )
            await writer.upsert(obj)
            count += 1
        except Exception:
            logger.exception("HuggingFace sync failed for %s", canonical)

    return count


async def sync_hn_algolia(ctx: dict) -> int:
    """Sync HN articles via Algolia (better search than RSS)."""
    pool: asyncpg.Pool = ctx["pool"]
    redis_client: aioredis.Redis = ctx["redis"]
    conn = HNAlgoliaConnector(redis_client)
    mapper = ArticleMapper()
    writer = OntologyWriter(pool)
    count = 0

    for company in COMPANIES:
        name = company["name"]
        try:
            results = await conn.fetch_search(name, limit=20)
            hits = results.get("hits", [])
            for hit in hits:
                article_raw = {
                    "title": hit.get("title", ""),
                    "url": hit.get("url", ""),
                    "published": hit.get("created_at", ""),
                    "score": hit.get("points", 0),
                    "comments": hit.get("num_comments", 0),
                }
                obj = mapper.from_hn(article_raw)
                article_id = await writer.upsert(obj)

                company_id = await writer.get_id("company", _canonical(company))
                if company_id:
                    await writer.upsert_link("mentions", article_id, company_id)
                count += 1
        except Exception:
            logger.exception("HN Algolia sync failed for %s", name)

    return count


async def sync_fred(ctx: dict) -> int:
    """Sync FRED macro-economic data (interest rates, inflation, GDP, WTI)."""
    from connectors.fred import FREDConnector
    from config import settings as _s
    from datetime import date as _date
    import json as _json

    if not _s.fred_api_key:
        logger.warning("FRED_API_KEY not set, skipping")
        return 0

    pool: asyncpg.Pool = ctx["pool"]
    redis_client: aioredis.Redis = ctx["redis"]
    conn = FREDConnector(redis_client, api_key=_s.fred_api_key)
    writer = OntologyWriter(pool)

    series_ids = ["DFF", "DGS10", "CPIAUCSL", "UNRATE", "GDP", "DCOILWTICO"]
    snapshot = {}
    for sid in series_ids:
        try:
            data = await conn.fetch_series(sid)
            obs = data.get("observations", [])
            snapshot[sid] = obs[0]["value"] if obs else None
        except Exception:
            logger.exception("FRED series %s failed", sid)

    from schemas.objects import EventObject
    obj = EventObject(
        key=f"macro-{_date.today()}",
        properties={
            "event_type": "macro_snapshot",
            "date": str(_date.today()),
            **snapshot,
        },
        sources={"fred": snapshot},
    )
    await writer.upsert(obj)
    return len(snapshot)


async def sync_eia(ctx: dict) -> int:
    """Sync EIA energy data (WTI, Brent, Natural Gas)."""
    from connectors.eia import EIAConnector
    from config import settings as _s

    if not _s.eia_api_key:
        logger.warning("EIA_API_KEY not set, skipping")
        return 0

    pool: asyncpg.Pool = ctx["pool"]
    redis_client: aioredis.Redis = ctx["redis"]
    conn = EIAConnector(redis_client, api_key=_s.eia_api_key)
    writer = OntologyWriter(pool)

    try:
        data = await conn.fetch_series("PET.RWTC.D")
        await writer.save_raw_snapshot("eia", "PET.RWTC.D", data)
        return 1
    except Exception:
        logger.exception("EIA sync failed")
        return 0


async def sync_forbes(ctx: dict) -> int:
    """Bulk-load Fortune 500 CSV as seed data."""
    pool: asyncpg.Pool = ctx["pool"]
    conn = ForbesConnector()
    mapper = CompanyMapper()
    writer = OntologyWriter(pool)

    records = await conn.fetch_all()
    count = 0
    for record in records:
        try:
            obj = mapper.from_forbes(record)
            await writer.upsert(obj)
            count += 1
        except Exception:
            logger.exception("Forbes sync failed for %s", record)

    return count


async def compute_derived(ctx: dict) -> int:
    """Compute derived properties for all companies."""
    pool: asyncpg.Pool = ctx["pool"]
    engine = DerivedPropertyEngine()
    count = 0

    async with pool.acquire() as conn:
        rows = await conn.fetch(
            "SELECT id, properties, sources FROM objects WHERE type = 'company'"
        )
        for row in rows:
            props = row["properties"] if isinstance(row["properties"], dict) else {}
            srcs = row["sources"] if isinstance(row["sources"], dict) else {}
            derived = engine.compute(props, srcs)
            await conn.execute(
                """
                UPDATE objects
                SET properties = properties || $1::jsonb, updated_at = now()
                WHERE id = $2
                """,
                __import__("json").dumps(derived),
                row["id"],
            )
            count += 1

    return count


async def resolve_entities(ctx: dict) -> int:
    """Merge duplicate companies into canonical keys using seed data."""
    import json as _json

    pool: asyncpg.Pool = ctx["pool"]
    count = 0

    # Build alias -> canonical mapping from seed data
    # Canonical key = company name lowercased (e.g. "apple", "google")
    alias_map: dict[str, str] = {}
    for company in COMPANIES:
        canonical = company["name"].lower()
        # All possible keys this company may have been inserted under
        aliases = set()
        aliases.add(canonical)
        if company.get("github"):
            aliases.add(company["github"].lower())
        if company.get("wiki"):
            aliases.add(company["wiki"].lower().replace("_", "-").replace(",", ""))
        if company.get("ticker"):
            aliases.add(company["ticker"].lower())
        for alias in aliases:
            if alias != canonical:
                alias_map[alias] = canonical

    # Also map SEC-style long names directly
    for company in COMPANIES:
        canonical = company["name"].lower()
        alias_map.setdefault(canonical, canonical)  # self-map for lookup

    SUFFIXES = [
        "-inc.", "-inc", "-corp", "-corporation", "-ltd.", "-ltd", "-llc",
        "-gmbh", "-ag", "-sa", "-plc", "-se", "-n.v.", "-pte.-ltd.", "-pte.-ltd",
        "-holdings-inc.", "-holdings-inc", "-holdings",
        "-technologies-inc.", "-technologies-inc", "-technologies",
        "-systems-inc.", "-systems-inc", "-systems",
        "-platforms-inc.", "-platforms-inc", "-platforms",
        "-communications-inc.", "-communications-inc", "-communications",
        "-networks-inc.", "-networks-inc", "-networks",
        "-com-inc", "-com", "/de",
    ]

    def _strip(key: str) -> str:
        """Iteratively strip known suffixes."""
        prev = None
        result = key
        while result != prev:
            prev = result
            for suffix in SUFFIXES:
                result = result.removesuffix(suffix)
            result = result.rstrip(".-")
        return result

    def _to_canonical(key: str) -> str:
        """Try multiple strategies to find canonical key."""
        if key in alias_map:
            return alias_map[key]
        stripped = _strip(key)
        if stripped in alias_map:
            return alias_map[stripped]
        # Check if any canonical name starts with stripped
        for company in COMPANIES:
            c = company["name"].lower()
            if c == stripped or c.replace(" ", "-") == stripped:
                return c
        return key

    async with pool.acquire() as conn:
        rows = await conn.fetch(
            "SELECT id, key, properties, sources FROM objects WHERE type = 'company' ORDER BY key"
        )

        # Group by canonical key
        groups: dict[str, list[dict]] = {}
        for row in rows:
            key = row["key"]
            canonical = _to_canonical(key)
            groups.setdefault(canonical, []).append(dict(row))

        for canonical, dupes in groups.items():
            if len(dupes) <= 1:
                continue

            # Merge all into one: combine properties + sources
            merged_props = {}
            merged_sources = {}
            primary_id = None
            for dupe in dupes:
                props = dupe["properties"] if isinstance(dupe["properties"], dict) else {}
                srcs = dupe["sources"] if isinstance(dupe["sources"], dict) else {}
                # Non-None values win
                for k, v in props.items():
                    if v is not None and (k not in merged_props or merged_props[k] is None):
                        merged_props[k] = v
                merged_sources.update(srcs)
                if dupe["key"] == canonical:
                    primary_id = dupe["id"]

            if not primary_id:
                primary_id = dupes[0]["id"]

            # Set canonical name if not set
            if "name" not in merged_props or not merged_props["name"]:
                for company in COMPANIES:
                    if company["name"].lower() == canonical:
                        merged_props["name"] = company["name"]
                        break

            # Update the primary record
            await conn.execute(
                """
                UPDATE objects
                SET key = $1, properties = $2::jsonb, sources = $3::jsonb, updated_at = now()
                WHERE id = $4
                """,
                canonical,
                _json.dumps(merged_props),
                _json.dumps(merged_sources),
                primary_id,
            )

            # Re-point all links from duplicates to the primary
            for dupe in dupes:
                if dupe["id"] == primary_id:
                    continue
                await conn.execute(
                    "UPDATE links SET from_id = $1 WHERE from_id = $2",
                    primary_id, dupe["id"],
                )
                await conn.execute(
                    "UPDATE links SET to_id = $1 WHERE to_id = $2",
                    primary_id, dupe["id"],
                )
                await conn.execute(
                    "DELETE FROM objects WHERE id = $1", dupe["id"]
                )
                count += 1

    return count
