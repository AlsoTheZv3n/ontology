"""Insights endpoints — anomalies, trending, movers, stats."""

from __future__ import annotations

from fastapi import APIRouter, Depends
import asyncpg

from api.deps import get_pool
from store.reader import OntologyReader
from transform.derived import EXPECTED_SOURCES

router = APIRouter()


@router.get("/anomalies")
async def anomalies(pool: asyncpg.Pool = Depends(get_pool)):
    """Companies with incomplete source coverage."""
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            """
            SELECT key, properties->>'name' as name, sources
            FROM objects
            WHERE type = 'company'
            ORDER BY updated_at DESC
            LIMIT 50
            """
        )

    results = []
    for row in rows:
        sources = row["sources"] if isinstance(row["sources"], dict) else {}
        missing = [s for s in EXPECTED_SOURCES if s not in sources]
        coverage = (len(EXPECTED_SOURCES) - len(missing)) / len(EXPECTED_SOURCES)
        if missing:
            results.append({
                "key": row["key"],
                "name": row["name"],
                "missing_sources": missing,
                "source_coverage": round(coverage, 2),
            })

    return results


@router.get("/top")
async def top_companies(
    metric: str = "market_cap",
    limit: int = 10,
    pool: asyncpg.Pool = Depends(get_pool),
):
    reader = OntologyReader(pool)
    return await reader.get_top_by_metric(metric, limit=limit)


@router.get("/trending")
async def trending(pool: asyncpg.Pool = Depends(get_pool)):
    """Companies ranked by HN mentions with 7d vs prev-7d trend."""
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            """
            SELECT
                o.key,
                o.properties->>'name' as name,
                COUNT(l.id) as total_mentions,
                COUNT(l.id) FILTER (
                    WHERE a.created_at >= now() - interval '7 days'
                ) as mentions_7d,
                COUNT(l.id) FILTER (
                    WHERE a.created_at >= now() - interval '14 days'
                      AND a.created_at < now() - interval '7 days'
                ) as mentions_prev_7d
            FROM objects o
            JOIN links l ON l.to_id = o.id AND l.type = 'mentions'
            JOIN objects a ON l.from_id = a.id AND a.type = 'article'
            WHERE o.type = 'company'
            GROUP BY o.id, o.key, o.properties
            HAVING COUNT(l.id) > 0
            ORDER BY total_mentions DESC
            LIMIT 10
            """
        )

    results = []
    for r in rows:
        curr = int(r["mentions_7d"] or 0)
        prev = int(r["mentions_prev_7d"] or 0)
        if prev == 0 and curr > 0:
            trend_pct = None  # no baseline → frontend shows "new"
        elif prev == 0:
            trend_pct = 0
        else:
            trend_pct = min(999, max(-99, round(((curr - prev) / prev) * 100)))
        results.append({
            "key": r["key"],
            "name": r["name"],
            "mentions": int(r["total_mentions"]),
            "mentions_7d": curr,
            "trend_pct": trend_pct,
        })
    return results


@router.get("/movers")
async def movers(pool: asyncpg.Pool = Depends(get_pool)):
    """Companies recently updated with most sources."""
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            """
            SELECT key, properties->>'name' as name,
                   properties->>'innovation_score' as score,
                   updated_at
            FROM objects
            WHERE type = 'company'
            ORDER BY updated_at DESC
            LIMIT 10
            """
        )
    return [
        {
            "key": r["key"],
            "name": r["name"],
            "score": r["score"],
            "updated": r["updated_at"].isoformat() if r["updated_at"] else None,
        }
        for r in rows
    ]


@router.get("/stale")
async def stale(hours: int = 24, pool: asyncpg.Pool = Depends(get_pool)):
    """Objects not updated in N hours."""
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            """
            SELECT key, type, properties->>'name' as name, updated_at
            FROM objects
            WHERE updated_at < now() - $1 * interval '1 hour'
            ORDER BY updated_at ASC
            LIMIT 20
            """,
            hours,
        )
    return [
        {
            "key": r["key"],
            "type": r["type"],
            "name": r["name"],
            "updated": r["updated_at"].isoformat() if r["updated_at"] else None,
        }
        for r in rows
    ]


@router.get("/stats")
async def stats(pool: asyncpg.Pool = Depends(get_pool)):
    """Dashboard KPIs."""
    async with pool.acquire() as conn:
        counts = await conn.fetch(
            "SELECT type, count(*) as count FROM objects GROUP BY type"
        )
        link_count = await conn.fetchval("SELECT count(*) FROM links")
        snapshot_count = await conn.fetchval("SELECT count(*) FROM raw_snapshots")
        source_counts = await conn.fetch(
            """
            SELECT s.key as source, count(*) as count
            FROM objects, jsonb_object_keys(sources) s(key)
            WHERE type = 'company'
            GROUP BY s.key
            ORDER BY count DESC
            """
        )

    return {
        "object_counts": {r["type"]: r["count"] for r in counts},
        "total_links": link_count,
        "total_snapshots": snapshot_count,
        "source_coverage": {r["source"]: r["count"] for r in source_counts},
    }


@router.get("/feed")
async def feed(limit: int = 30, pool: asyncpg.Pool = Depends(get_pool)):
    """Recent events stream — filings, articles, anomalies sorted by time."""
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            """
            SELECT key, type,
                   properties->>'name' as name,
                   properties->>'title' as title,
                   properties->>'event_type' as event_type,
                   properties->>'form' as form,
                   properties->>'date' as event_date,
                   properties->>'source' as source,
                   updated_at
            FROM objects
            WHERE type IN ('event', 'article')
            ORDER BY updated_at DESC
            LIMIT $1
            """,
            limit,
        )
    return [
        {
            "key": r["key"],
            "type": r["type"],
            "label": r["title"] or r["name"] or (f"{r['form']} — {r['event_date']}" if r["form"] else r["key"]),
            "event_type": r["event_type"] or r["source"] or r["type"],
            "date": r["event_date"],
            "updated": r["updated_at"].isoformat() if r["updated_at"] else None,
        }
        for r in rows
    ]


@router.get("/schema")
async def schema(pool: asyncpg.Pool = Depends(get_pool)):
    """Ontology schema — link types with counts and from/to types."""
    async with pool.acquire() as conn:
        link_stats = await conn.fetch(
            """
            SELECT l.type as link_type,
                   o_from.type as from_type,
                   o_to.type as to_type,
                   count(*) as count
            FROM links l
            JOIN objects o_from ON l.from_id = o_from.id
            JOIN objects o_to ON l.to_id = o_to.id
            GROUP BY l.type, o_from.type, o_to.type
            ORDER BY count DESC
            """
        )
        type_counts = await conn.fetch(
            "SELECT type, count(*) as count FROM objects GROUP BY type ORDER BY count DESC"
        )
    return {
        "link_types": [
            {
                "type": r["link_type"],
                "from_type": r["from_type"],
                "to_type": r["to_type"],
                "count": r["count"],
            }
            for r in link_stats
        ],
        "object_types": [
            {"type": r["type"], "count": r["count"]}
            for r in type_counts
        ],
    }


@router.get("/entities")
async def entities(
    type: str = "company",
    limit: int = 50,
    offset: int = 0,
    pool: asyncpg.Pool = Depends(get_pool),
):
    """Browse entities by type with key properties."""
    async with pool.acquire() as conn:
        total = await conn.fetchval(
            "SELECT count(*) FROM objects WHERE type = $1", type
        )
        rows = await conn.fetch(
            """
            SELECT key, properties->>'name' as name, sources, updated_at
            FROM objects
            WHERE type = $1
            ORDER BY properties->>'name' NULLS LAST, key
            LIMIT $2 OFFSET $3
            """,
            type, limit, offset,
        )
    return {
        "type": type,
        "total": total,
        "items": [
            {
                "key": r["key"],
                "name": r["name"] or r["key"],
                "sources": list(r["sources"].keys()) if isinstance(r["sources"], dict) else [],
                "updated": r["updated_at"].isoformat() if r["updated_at"] else None,
            }
            for r in rows
        ],
    }


@router.get("/markets")
async def markets(pool: asyncpg.Pool = Depends(get_pool)):
    """Macro indicators and commodity-related data."""
    async with pool.acquire() as conn:
        macro = await conn.fetch(
            """
            SELECT key, properties->>'name' as name,
                   properties->>'indicator' as indicator,
                   properties->>'country' as country,
                   properties->>'latest_value' as value,
                   properties->>'latest_year' as year
            FROM objects
            WHERE type = 'macro_indicator'
            ORDER BY properties->>'country', properties->>'indicator'
            """
        )
        top_companies = await conn.fetch(
            """
            SELECT key, properties->>'name' as name,
                   properties->>'market_cap' as market_cap,
                   properties->>'revenue' as revenue,
                   properties->>'net_income' as net_income,
                   properties->>'sector' as sector
            FROM objects
            WHERE type = 'company' AND properties->>'market_cap' IS NOT NULL
            ORDER BY (properties->>'market_cap')::float DESC NULLS LAST
            LIMIT 15
            """
        )
    return {
        "macro_indicators": [dict(r) for r in macro],
        "top_companies": [dict(r) for r in top_companies],
    }


@router.get("/alerts")
async def alerts(pool: asyncpg.Pool = Depends(get_pool)):
    """Generate live alerts from Z-score anomaly detection on company metrics."""
    from ml.analytics import detect_anomalies
    import numpy as np

    METRICS = [
        ("github_repos", "GitHub Activity", "GitHub"),
        ("hf_model_count", "HuggingFace Models", "HuggingFace"),
        ("revenue", "Revenue Outlier", "SEC XBRL"),
        ("market_cap", "Market Cap Anomaly", "Alpha Vantage"),
        ("rd_expense", "R&D Spending Anomaly", "SEC XBRL"),
    ]

    all_alerts = []

    async with pool.acquire() as conn:
        for metric, label, source in METRICS:
            rows = await conn.fetch(f"""
                SELECT key, properties->>'name' as name,
                       (properties->>'{metric}')::float as val
                FROM objects WHERE type='company' AND properties->>'{metric}' IS NOT NULL
                ORDER BY key
            """)
            if len(rows) < 5:
                continue

            values = [r["val"] for r in rows]
            mean = np.mean(values)
            std = np.std(values)
            if std == 0:
                continue

            anomaly_indices = detect_anomalies(values, sensitivity=1.8)
            for idx in anomaly_indices:
                r = rows[idx]
                z = abs((r["val"] - mean) / std)
                severity = "high" if z > 3 else "medium" if z > 2.5 else "low"
                val_fmt = f"${r['val']/1e9:.1f}B" if r["val"] > 1e9 else f"{r['val']:,.0f}"
                avg_fmt = f"${mean/1e9:.1f}B" if mean > 1e9 else f"{mean:,.0f}"
                all_alerts.append({
                    "id": f"alert-{metric}-{r['key']}",
                    "title": f"{r['name'] or r['key']} — {label}",
                    "description": f"{metric.replace('_',' ').title()} value {val_fmt} is {z:.1f}σ from mean ({avg_fmt}). Statistical outlier detected across {len(rows)} companies.",
                    "severity": severity,
                    "source": source,
                    "company_key": r["key"],
                    "metric": metric,
                    "value": r["val"],
                    "z_score": round(z, 2),
                })

    # Sort by severity then z_score
    sev_order = {"high": 0, "medium": 1, "low": 2}
    all_alerts.sort(key=lambda a: (sev_order.get(a["severity"], 3), -a["z_score"]))
    return all_alerts[:20]


@router.get("/clusters")
async def clusters(pool: asyncpg.Pool = Depends(get_pool)):
    """Company clusters from K-Means clustering."""
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            """
            SELECT key, properties->>'name' as name,
                   properties->>'cluster_id' as cluster_id
            FROM objects
            WHERE type = 'company' AND properties->>'cluster_id' IS NOT NULL
            ORDER BY (properties->>'cluster_id')::int, properties->>'name'
            """
        )
    result: dict[str, list] = {}
    for r in rows:
        cid = r["cluster_id"] or "unknown"
        result.setdefault(f"cluster_{cid}", []).append(
            {"key": r["key"], "name": r["name"]}
        )
    return result


@router.get("/sentiment/{company_key}")
async def sentiment_trend(company_key: str, pool: asyncpg.Pool = Depends(get_pool)):
    """Aggregated sentiment from articles mentioning a company."""
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            """
            SELECT a.properties->>'title' as title,
                   (a.properties->>'sentiment')::float as sentiment,
                   a.properties->>'sentiment_label' as label,
                   a.updated_at
            FROM links l
            JOIN objects a ON l.from_id = a.id AND a.type = 'article'
            JOIN objects c ON l.to_id = c.id AND c.type = 'company'
            WHERE c.key = $1 AND l.type = 'mentions'
              AND a.properties->>'sentiment' IS NOT NULL
            ORDER BY a.updated_at DESC
            LIMIT 30
            """,
            company_key,
        )
    articles = [
        {
            "title": r["title"],
            "sentiment": r["sentiment"],
            "label": r["label"],
            "date": r["updated_at"].isoformat() if r["updated_at"] else None,
        }
        for r in rows
    ]
    avg = sum(r["sentiment"] for r in rows) / len(rows) if rows else 0
    return {
        "company": company_key,
        "avg_sentiment": round(avg, 3),
        "article_count": len(articles),
        "articles": articles,
    }


@router.get("/forecast/{company_key}/{metric}")
async def forecast(
    company_key: str,
    metric: str,
    periods: int = 4,
    pool: asyncpg.Pool = Depends(get_pool),
):
    """Linear forecast for a company metric."""
    from ml.analytics import forecast_linear

    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            "SELECT properties FROM objects WHERE type='company' AND key=$1",
            company_key,
        )
    if not row:
        return {"error": "Company not found"}

    props = row["properties"] if isinstance(row["properties"], dict) else {}
    value = props.get(metric)
    if value is None:
        return {"error": f"Metric '{metric}' not found"}

    # Simple forecast from single value (linear extrapolation)
    forecasts = forecast_linear([float(value)], periods=periods)
    return {
        "company": company_key,
        "metric": metric,
        "current": value,
        "forecast": forecasts,
    }
