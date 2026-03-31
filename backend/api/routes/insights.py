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
