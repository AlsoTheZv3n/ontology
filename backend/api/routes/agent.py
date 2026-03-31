"""Agent Layer — Claude tool definitions + agentic loop."""

from __future__ import annotations

import asyncio
import json
import logging
from typing import AsyncIterator

import anthropic
import asyncpg
import feedparser
import httpx

from config import settings
from store.reader import OntologyReader

logger = logging.getLogger(__name__)

client = anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key)

# ─────────────────────────────────────────────
# Tool definitions (what Claude sees)
# ─────────────────────────────────────────────

TOOLS = [
    {
        "name": "search_objects",
        "description": (
            "Suche nach Objekten in der Ontology-Datenbank. "
            "Gibt Companies, Persons, Articles, Repos oder Events zurück. "
            "Nutze dies als ersten Schritt um relevante Objekte zu finden."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Suchbegriff, z.B. 'artificial intelligence' oder 'Apple'"
                },
                "type": {
                    "type": "string",
                    "enum": ["company", "person", "article", "repository", "event"],
                    "description": "Optional: Filter nach Object Type"
                },
                "limit": {
                    "type": "integer",
                    "default": 10,
                    "description": "Maximale Anzahl Ergebnisse (default: 10, max: 50)"
                }
            },
            "required": ["query"]
        }
    },
    {
        "name": "get_object",
        "description": (
            "Gibt ein vollständiges Objekt mit allen Properties und Quellen zurück. "
            "Nutze dies nach search_objects um Details zu bekommen."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "key": {
                    "type": "string",
                    "description": "Der Object Key, z.B. 'apple', 'microsoft'"
                }
            },
            "required": ["key"]
        }
    },
    {
        "name": "get_links",
        "description": (
            "Gibt alle verbundenen Objekte eines Eintrags zurück. "
            "Z.B. alle Repos einer Company (owns_repo), "
            "alle Artikel die eine Company erwähnen (mentions)."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "key": {
                    "type": "string",
                    "description": "Object Key des Ausgangsobjekts"
                },
                "link_type": {
                    "type": "string",
                    "description": "Optional: Filter nach Link-Typ (owns_repo, mentions, is_ceo_of, filed)"
                },
                "limit": {
                    "type": "integer",
                    "default": 20
                }
            },
            "required": ["key"]
        }
    },
    {
        "name": "compare_objects",
        "description": (
            "Vergleicht mehrere Objekte nach bestimmten Properties. "
            "Ideal für Fragen wie 'Vergleich Anthropic und OpenAI'."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "keys": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Liste von Object Keys, z.B. ['apple', 'microsoft', 'google']"
                },
                "metrics": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Optional: Properties zum Vergleich, z.B. ['market_cap', 'github_stars']"
                }
            },
            "required": ["keys"]
        }
    },
    {
        "name": "get_anomalies",
        "description": (
            "Findet Objekte mit fehlenden Datenquellen. "
            "Z.B. Companies wo SEC-Daten fehlen."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "type": {
                    "type": "string",
                    "enum": ["company", "person", "article", "repository", "event"],
                    "description": "Optional: Filter nach Object Type"
                },
                "missing_source": {
                    "type": "string",
                    "description": "Optional: Nur Objekte wo diese Quelle fehlt (wikipedia, github, yahoo_finance, sec_edgar, hn_rss, patents, forbes)"
                },
                "limit": {
                    "type": "integer",
                    "default": 20
                }
            }
        }
    },
    {
        "name": "get_timeline",
        "description": (
            "Gibt alle Events einer Company chronologisch zurück: "
            "SEC-Filings, Patente, HN-Peaks."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "key": {
                    "type": "string",
                    "description": "Company Key"
                }
            },
            "required": ["key"]
        }
    },
    {
        "name": "rank_objects",
        "description": (
            "Rankt Objekte nach einer Property. "
            "Ideal für 'Top 5 Companies nach GitHub Stars'."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "metric": {
                    "type": "string",
                    "description": "Property zum Ranken: github_stars, market_cap, employees, innovation_score, github_repos"
                },
                "type": {
                    "type": "string",
                    "default": "company"
                },
                "limit": {
                    "type": "integer",
                    "default": 10
                }
            },
            "required": ["metric"]
        }
    },
    {
        "name": "get_market_data",
        "description": (
            "Holt live Marktdaten inkl. Kursverlauf und technische Indikatoren. "
            "Ticker-Symbole: AAPL, MSFT, TSLA (Aktien), CL=F (WTI Öl), GC=F (Gold), "
            "SI=F (Silber), NG=F (Erdgas), BTC-USD (Bitcoin), ETH-USD (Ethereum), "
            "^GSPC (S&P 500), ^DJI (Dow), ^IXIC (NASDAQ), ^GDAXI (DAX), "
            "EURUSD=X (EUR/USD). Gibt Kurs, Veränderung, Trend-Analyse und "
            "Kursverlauf der letzten 30 Tage zurück."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "symbols": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Ticker-Symbole, z.B. ['CL=F', 'GC=F', '^GSPC']"
                },
                "range": {
                    "type": "string",
                    "default": "1mo",
                    "description": "Zeitraum: 1d, 5d, 1mo, 3mo, 6mo, 1y, 5y"
                }
            },
            "required": ["symbols"]
        }
    },
    {
        "name": "search_news",
        "description": (
            "Sucht aktuelle Nachrichten zu einem Thema via Google News RSS. "
            "Ideal für Fragen zu aktuellen Events, Geopolitik, Märkten, "
            "Kriegen, Wirtschaft — alles was nicht in der Ontology-DB steht."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Suchbegriff, z.B. 'Iran war', 'oil prices', 'AI regulation'"
                },
                "language": {
                    "type": "string",
                    "default": "en",
                    "description": "Sprache: 'en', 'de', 'fr' etc."
                },
                "limit": {
                    "type": "integer",
                    "default": 10
                }
            },
            "required": ["query"]
        }
    },
    {
        "name": "search_research",
        "description": (
            "Sucht akademische Papers und AI-Modelle. "
            "Kombiniert ArXiv (wissenschaftliche Papers) und HuggingFace (AI-Modelle). "
            "Ideal für Fragen zu AI-Forschung, ML-Modellen, und wissenschaftlichen Trends."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Suchbegriff, z.B. 'transformer architecture', 'LLM reasoning'"
                },
                "source": {
                    "type": "string",
                    "enum": ["arxiv", "huggingface", "both"],
                    "default": "both"
                },
                "limit": {"type": "integer", "default": 10}
            },
            "required": ["query"]
        }
    },
    {
        "name": "get_package_stats",
        "description": (
            "Holt Statistiken zu Open-Source-Paketen von npm oder PyPI. "
            "Ideal für Fragen wie 'Wie viele Downloads hat React?' oder 'Welche Version hat FastAPI?'"
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "name": {
                    "type": "string",
                    "description": "Paketname, z.B. 'react', 'fastapi', 'langchain'"
                },
                "registry": {
                    "type": "string",
                    "enum": ["npm", "pypi", "both"],
                    "default": "both"
                }
            },
            "required": ["name"]
        }
    },
    {
        "name": "get_sentiment_trend",
        "description": (
            "FinBERT-Sentiment-Trend für eine Company basierend auf Artikeln. "
            "Gibt Durchschnitts-Sentiment und einzelne Artikel-Bewertungen zurück."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "company_key": {"type": "string", "description": "Company Key"}
            },
            "required": ["company_key"]
        }
    },
    {
        "name": "get_clusters",
        "description": "Company-Cluster aus K-Means Clustering nach Finanz- und Tech-Profil.",
        "input_schema": {"type": "object", "properties": {}}
    },
    {
        "name": "detect_anomalies_metric",
        "description": (
            "Statistische Anomalie-Erkennung (Z-Score) für einen Metric über alle Companies. "
            "Findet Ausreisser bei GitHub-Repos, Revenue, Market Cap etc."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "metric": {"type": "string", "description": "Property name: github_repos, revenue, market_cap, etc."}
            },
            "required": ["metric"]
        }
    }
]


# ─────────────────────────────────────────────
# Tool execution — maps tool names to DB queries
# ─────────────────────────────────────────────

async def execute_tool(name: str, inputs: dict, reader: OntologyReader) -> dict:
    """Execute a tool call against the real DB."""
    logger.info("Tool: %s | Input: %s", name, inputs)

    if name == "search_objects":
        results = await reader.search(
            query=inputs["query"],
            obj_type=inputs.get("type"),
            limit=min(inputs.get("limit", 10), 50),
        )
        compact = [
            {
                "key": r.get("key"),
                "type": r.get("type"),
                "name": (r.get("properties") or {}).get("name") if isinstance(r.get("properties"), dict) else None,
            }
            for r in results
        ]
        return {"results": compact, "count": len(compact)}

    elif name == "get_object":
        obj = await reader.get_object(inputs["key"])
        if not obj:
            return {"error": f"Object '{inputs['key']}' not found"}
        props = obj.get("properties", {})
        props = props if isinstance(props, dict) else {}
        srcs = obj.get("sources", {})
        srcs = srcs if isinstance(srcs, dict) else {}
        return {
            "key": obj["key"],
            "type": obj["type"],
            "properties": props,
            "present_sources": list(srcs.keys()),
        }

    elif name == "get_links":
        links = await reader.get_links(inputs["key"])
        limited = links[: inputs.get("limit", 20)]
        compact = [
            {
                "link_type": l.get("type"),
                "key": l.get("to_key") if l.get("from_key") == inputs["key"] else l.get("from_key"),
                "object_type": l.get("to_type") if l.get("from_key") == inputs["key"] else l.get("from_type"),
            }
            for l in limited
        ]
        if inputs.get("link_type"):
            compact = [c for c in compact if c["link_type"] == inputs["link_type"]]
        return {"links": compact, "count": len(compact)}

    elif name == "compare_objects":
        objects = []
        for key in inputs["keys"]:
            obj = await reader.get_object(key)
            if not obj:
                objects.append({"key": key, "error": "not found"})
                continue
            props = obj.get("properties", {})
            props = props if isinstance(props, dict) else {}
            if inputs.get("metrics"):
                filtered = {"key": key}
                for m in inputs["metrics"]:
                    filtered[m] = props.get(m)
                objects.append(filtered)
            else:
                objects.append({"key": key, "properties": props})
        return {"comparison": objects}

    elif name == "get_anomalies":
        items, total = await reader.list_objects(
            obj_type=inputs.get("type", "company"),
            missing_source=inputs.get("missing_source"),
            limit=inputs.get("limit", 20),
        )
        compact = []
        for item in items:
            props = item.get("properties", {})
            props = props if isinstance(props, dict) else {}
            srcs = item.get("sources", {})
            srcs = srcs if isinstance(srcs, dict) else {}
            compact.append({
                "key": item["key"],
                "name": props.get("name"),
                "present_sources": list(srcs.keys()),
                "source_coverage": props.get("source_coverage"),
                "missing_sources": props.get("missing_sources"),
            })
        return {"anomalies": compact, "count": len(compact)}

    elif name == "get_timeline":
        events = await reader.get_timeline(inputs["key"])
        compact = []
        for e in events:
            props = e.get("properties", {})
            props = props if isinstance(props, dict) else {}
            compact.append({
                "key": e["key"],
                "event_type": props.get("event_type"),
                "date": props.get("date"),
                "title": props.get("title"),
                "form": props.get("form"),
            })
        return {"timeline": compact, "count": len(compact)}

    elif name == "rank_objects":
        results = await reader.get_top_by_metric(
            metric=inputs["metric"],
            limit=inputs.get("limit", 10),
        )
        ranked = [
            {"rank": i + 1, "key": r["key"], "name": r["name"], "value": r["value"]}
            for i, r in enumerate(results)
        ]
        return {"ranking": ranked, "metric": inputs["metric"]}

    elif name == "get_market_data":
        results = []
        period = inputs.get("range", "1mo")
        headers = {"User-Agent": "Mozilla/5.0 (Sovereign Ontology)"}
        async with httpx.AsyncClient(timeout=15, headers=headers) as http:
            for symbol in inputs["symbols"][:10]:
                try:
                    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}?range={period}&interval=1d"
                    resp = await http.get(url)
                    resp.raise_for_status()
                    data = resp.json()
                    result = data["chart"]["result"][0]
                    meta = result["meta"]
                    timestamps = result.get("timestamp", [])
                    closes = result.get("indicators", {}).get("quote", [{}])[0].get("close", [])

                    # Clean None values
                    prices = [p for p in closes if p is not None]

                    # Compute trend indicators
                    current = meta.get("regularMarketPrice")
                    prev_close = meta.get("previousClose") or meta.get("chartPreviousClose")
                    change = (current - prev_close) if current and prev_close else None
                    change_pct = (change / prev_close * 100) if change and prev_close else None

                    # Simple moving averages
                    sma_5 = sum(prices[-5:]) / min(5, len(prices)) if len(prices) >= 5 else None
                    sma_20 = sum(prices[-20:]) / min(20, len(prices)) if len(prices) >= 20 else None

                    # Period high/low
                    period_high = max(prices) if prices else None
                    period_low = min(prices) if prices else None

                    # Trend direction
                    if len(prices) >= 5:
                        recent_avg = sum(prices[-3:]) / 3
                        older_avg = sum(prices[-8:-3]) / 5 if len(prices) >= 8 else prices[0]
                        trend = "bullish" if recent_avg > older_avg else "bearish"
                    else:
                        trend = "insufficient data"

                    results.append({
                        "symbol": symbol,
                        "name": meta.get("longName") or meta.get("shortName") or symbol,
                        "currency": meta.get("currency"),
                        "price": round(current, 2) if current else None,
                        "previous_close": round(prev_close, 2) if prev_close else None,
                        "change": round(change, 2) if change else None,
                        "change_pct": round(change_pct, 2) if change_pct else None,
                        "period_high": round(period_high, 2) if period_high else None,
                        "period_low": round(period_low, 2) if period_low else None,
                        "sma_5": round(sma_5, 2) if sma_5 else None,
                        "sma_20": round(sma_20, 2) if sma_20 else None,
                        "trend": trend,
                        "data_points": len(prices),
                    })
                except Exception as e:
                    results.append({"symbol": symbol, "error": str(e)})
        return {"quotes": results, "count": len(results)}

    elif name == "search_news":
        query = inputs["query"]
        lang = inputs.get("language", "en")
        limit = min(inputs.get("limit", 10), 20)
        encoded = query.replace(" ", "+")
        url = f"https://news.google.com/rss/search?q={encoded}&hl={lang}&gl=US&ceid=US:en"
        try:
            headers = {"User-Agent": "Mozilla/5.0 (Sovereign Ontology)"}
            async with httpx.AsyncClient(timeout=15, headers=headers, follow_redirects=True) as http:
                resp = await http.get(url)
                resp.raise_for_status()
                text = resp.text

            loop = asyncio.get_event_loop()
            feed = await loop.run_in_executor(None, feedparser.parse, text)

            articles = []
            for entry in feed.entries[:limit]:
                articles.append({
                    "title": entry.get("title", ""),
                    "source": entry.get("source", {}).get("title", "") if isinstance(entry.get("source"), dict) else "",
                    "published": entry.get("published", ""),
                })
            return {"articles": articles, "count": len(articles)}
        except Exception as e:
            return {"error": str(e), "count": 0}

    elif name == "search_research":
        import redis.asyncio as aioredis
        from config import settings as _s
        results: dict = {}
        redis_client = aioredis.from_url(_s.redis_url)
        try:
            source = inputs.get("source", "both")
            limit = min(inputs.get("limit", 10), 20)

            if source in ("arxiv", "both"):
                from connectors.arxiv import ArxivConnector
                arxiv = ArxivConnector(redis_client)
                papers = await arxiv.fetch_papers(inputs["query"], max_results=limit)
                results["arxiv_papers"] = [
                    {"title": p["title"], "authors": p.get("authors", [])[:3], "published": p.get("published"), "arxiv_id": p.get("arxiv_id")}
                    for p in papers
                ]

            if source in ("huggingface", "both"):
                from connectors.huggingface import HuggingFaceConnector
                hf = HuggingFaceConnector(redis_client)
                models = await hf.fetch_models(inputs["query"])
                model_list = models if isinstance(models, list) else []
                results["hf_models"] = [
                    {"id": m.get("modelId") or m.get("id"), "downloads": m.get("downloads"), "likes": m.get("likes")}
                    for m in model_list[:limit]
                ]
        finally:
            await redis_client.close()
        results["count"] = sum(len(v) for v in results.values() if isinstance(v, list))
        return results

    elif name == "get_package_stats":
        import redis.asyncio as aioredis
        from config import settings as _s
        redis_client = aioredis.from_url(_s.redis_url)
        results: dict = {"packages": []}
        try:
            registry = inputs.get("registry", "both")
            pkg_name = inputs["name"]

            if registry in ("npm", "both"):
                from connectors.npm_registry import NpmRegistryConnector
                npm = NpmRegistryConnector(redis_client)
                try:
                    info = await npm.fetch_package(pkg_name)
                    dl = await npm.fetch_downloads(pkg_name)
                    results["packages"].append({
                        "registry": "npm",
                        "name": pkg_name,
                        "version": info.get("dist-tags", {}).get("latest"),
                        "description": info.get("description", "")[:200],
                        "monthly_downloads": dl.get("downloads"),
                    })
                except Exception:
                    results["packages"].append({"registry": "npm", "name": pkg_name, "error": "not found"})

            if registry in ("pypi", "both"):
                from connectors.pypi import PyPIConnector
                pypi = PyPIConnector(redis_client)
                try:
                    info = await pypi.fetch_package(pkg_name)
                    pi = info.get("info", {})
                    results["packages"].append({
                        "registry": "pypi",
                        "name": pkg_name,
                        "version": pi.get("version"),
                        "description": (pi.get("summary") or "")[:200],
                        "author": pi.get("author"),
                    })
                except Exception:
                    results["packages"].append({"registry": "pypi", "name": pkg_name, "error": "not found"})
        finally:
            await redis_client.close()
        results["count"] = len(results["packages"])
        return results

    elif name == "get_sentiment_trend":
        company_key = inputs["company_key"]
        async with reader.pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT a.properties->>'title' as title,
                       (a.properties->>'sentiment')::float as sentiment,
                       a.properties->>'sentiment_label' as label
                FROM links l
                JOIN objects a ON l.from_id = a.id AND a.type = 'article'
                JOIN objects c ON l.to_id = c.id AND c.type = 'company'
                WHERE c.key = $1 AND l.type = 'mentions'
                  AND a.properties->>'sentiment' IS NOT NULL
                ORDER BY a.updated_at DESC LIMIT 20
                """,
                company_key,
            )
        articles = [{"title": r["title"], "sentiment": r["sentiment"], "label": r["label"]} for r in rows]
        avg = sum(r["sentiment"] for r in rows) / len(rows) if rows else 0
        return {"company": company_key, "avg_sentiment": round(avg, 3), "count": len(articles), "articles": articles[:10]}

    elif name == "get_clusters":
        async with reader.pool.acquire() as conn:
            rows = await conn.fetch("""
                SELECT key, properties->>'name' as name, properties->>'cluster_id' as cluster_id
                FROM objects WHERE type='company' AND properties->>'cluster_id' IS NOT NULL
                ORDER BY (properties->>'cluster_id')::int
            """)
        clusters: dict = {}
        for r in rows:
            clusters.setdefault(f"cluster_{r['cluster_id']}", []).append({"key": r["key"], "name": r["name"]})
        return {"clusters": clusters, "count": len(rows)}

    elif name == "detect_anomalies_metric":
        from ml.analytics import detect_anomalies
        metric = inputs["metric"]
        async with reader.pool.acquire() as conn:
            rows = await conn.fetch(f"""
                SELECT key, properties->>'name' as name, (properties->>'{metric}')::float as val
                FROM objects WHERE type='company' AND properties->>'{metric}' IS NOT NULL
                ORDER BY key
            """)
        if not rows:
            return {"error": f"No data for metric '{metric}'"}
        values = [r["val"] for r in rows]
        anomaly_indices = detect_anomalies(values)
        anomalies = [{"key": rows[i]["key"], "name": rows[i]["name"], "value": rows[i]["val"]} for i in anomaly_indices]
        return {"metric": metric, "anomalies": anomalies, "count": len(anomalies), "total_companies": len(rows)}

    return {"error": f"Unknown tool: {name}"}


# ─────────────────────────────────────────────
# Agentic loop with streaming events
# ─────────────────────────────────────────────

SYSTEM_PROMPT = """Du bist Sovereign, ein Intelligence-Agent mit Zugriff auf:

1. **Ontology-Datenbank** (PostgreSQL) — Tech-Unternehmen:
   - Companies (market_cap, employees, sector, github_stars, patent_count, innovation_score)
   - Articles (HN-Erwähnungen), Repositories (GitHub), Events (SEC-Filings, Patente)
   - Quellen: wikipedia, yahoo_finance, github, sec_edgar, hn_rss, forbes, patents

2. **Live Marktdaten** (get_market_data) — Aktien, Rohstoffe, Indizes, Crypto, Forex:
   - Aktien: AAPL, MSFT, TSLA, etc.
   - Rohstoffe: CL=F (WTI Öl), GC=F (Gold), SI=F (Silber), NG=F (Gas)
   - Indizes: ^GSPC (S&P 500), ^DJI (Dow), ^IXIC (NASDAQ), ^GDAXI (DAX)
   - Crypto: BTC-USD, ETH-USD
   - Forex: EURUSD=X, GBPUSD=X

3. **Aktuelle Nachrichten** (search_news) — Google News RSS:
   - Geopolitik, Kriege, Wirtschaft, Politik, Sport, Wissenschaft
   - Beliebige Sprache und Themen

Regeln:
1. Nutze IMMER zuerst Tools — antworte nie aus dem Gedächtnis wenn es um Fakten/Daten geht
2. Zitiere Quellen (z.B. "laut yahoo_finance", "laut Google News")
3. Wenn Daten fehlen (null), sage es explizit — erfinde keine Zahlen
4. Antworte in der Sprache der Frage
5. Zeige konkrete Zahlen mit Einheit und Prozent-Veränderungen
6. Bei Vergleichen: nutze compare_objects statt mehrere get_object Calls
7. Für Fragen ausserhalb der Ontology (Öl, Gold, Politik, Kriege): nutze get_market_data und search_news

Formatierung (Markdown):
- Nutze **fett** für wichtige Zahlen und Namen
- Nutze Tabellen für Vergleiche mehrerer Assets
- Nutze Überschriften (##) für Abschnitte
- Nutze Bullet-Points für Listen

Bei Finanz- und Marktfragen:
- Zeige IMMER: aktuellen Preis, Veränderung % (heute), Trend (bullish/bearish)
- Nutze Tabellen-Format: | Asset | Preis | Änderung | Trend |
- Vergleiche mit historischem Kontext (5d/20d Durchschnitt)
- Zitiere News-Headlines die den Preis erklären
- Gib am Ende eine Einschätzung (bullish/bearish/neutral) mit Begründung
- Wenn der User nach Predictions fragt: basiere auf Trend-Daten + News, sage klar dass es keine Garantie ist"""


async def run_agent_stream(
    question: str,
    pool: asyncpg.Pool,
) -> AsyncIterator[dict]:
    """
    Agentic loop with streaming.
    Yields: {"type": "tool_call"|"tool_result"|"text"|"done", ...}
    """
    reader = OntologyReader(pool)
    messages = [{"role": "user", "content": question}]

    for _ in range(10):  # max iterations safety
        response = await client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=4096,
            system=SYSTEM_PROMPT,
            tools=TOOLS,
            messages=messages,
        )

        # No tool calls → final answer
        if response.stop_reason == "end_turn":
            for block in response.content:
                if hasattr(block, "text"):
                    yield {"type": "text", "content": block.text}
            yield {"type": "done"}
            return

        # Process tool calls
        tool_results = []
        for block in response.content:
            if block.type != "tool_use":
                continue

            yield {"type": "tool_call", "name": block.name, "input": block.input}

            result = await execute_tool(block.name, block.input, reader)

            yield {"type": "tool_result", "name": block.name, "result": result}

            tool_results.append({
                "type": "tool_result",
                "tool_use_id": block.id,
                "content": json.dumps(result, default=str),
            })

        messages.append({"role": "assistant", "content": response.content})
        messages.append({"role": "user", "content": tool_results})

    yield {"type": "text", "content": "Max iterations reached."}
    yield {"type": "done"}
