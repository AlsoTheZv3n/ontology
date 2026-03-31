"""Search endpoint — full-text search + pgvector similarity + autocomplete."""

from __future__ import annotations

from fastapi import APIRouter, Depends
import asyncpg

from api.deps import get_pool
from store.reader import OntologyReader

router = APIRouter()


@router.get("/suggest")
async def suggest(
    q: str,
    limit: int = 8,
    pool: asyncpg.Pool = Depends(get_pool),
):
    """Fast autocomplete suggestions based on prefix match."""
    if len(q) < 1:
        return []
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            """
            SELECT key, type,
                   COALESCE(properties->>'name', key) as name
            FROM objects
            WHERE key ILIKE $1 OR properties->>'name' ILIKE $1
            ORDER BY
                CASE WHEN key = $2 THEN 0
                     WHEN key ILIKE $3 THEN 1
                     WHEN properties->>'name' ILIKE $3 THEN 2
                     ELSE 3 END,
                CASE type WHEN 'company' THEN 0 WHEN 'person' THEN 1 ELSE 2 END,
                length(key) ASC
            LIMIT $4
            """,
            f"%{q}%",
            q.lower(),
            f"{q}%",
            limit,
        )
        return [
            {"key": r["key"], "type": r["type"], "name": r["name"] or r["key"]}
            for r in rows
        ]


@router.get("")
async def search(
    q: str,
    type: str | None = None,
    limit: int = 20,
    pool: asyncpg.Pool = Depends(get_pool),
):
    reader = OntologyReader(pool)
    results = await reader.search(q, obj_type=type, limit=limit)
    return [_serialize(r) for r in results]


@router.get("/similar/{key}")
async def similar(
    key: str,
    limit: int = 5,
    pool: asyncpg.Pool = Depends(get_pool),
):
    reader = OntologyReader(pool)
    results = await reader.get_similar(key, limit=limit)
    return [_serialize(r) for r in results]


def _serialize(row: dict) -> dict:
    result = {}
    for k, v in row.items():
        if hasattr(v, "isoformat"):
            result[k] = v.isoformat()
        else:
            result[k] = v
    return result
