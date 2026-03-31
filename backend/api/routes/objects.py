"""CRUD endpoints for ontology objects."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
import asyncpg

from api.deps import get_pool
from store.reader import OntologyReader

router = APIRouter()


@router.get("")
async def list_objects(
    type: str | None = None,
    missing: str | None = None,
    limit: int = 50,
    offset: int = 0,
    pool: asyncpg.Pool = Depends(get_pool),
):
    reader = OntologyReader(pool)
    items, total = await reader.list_objects(
        obj_type=type, missing_source=missing, limit=limit, offset=offset
    )
    return {
        "items": [_serialize(r) for r in items],
        "total": total,
    }


@router.get("/{key}")
async def get_object(key: str, pool: asyncpg.Pool = Depends(get_pool)):
    reader = OntologyReader(pool)
    obj = await reader.get_object(key)
    if not obj:
        raise HTTPException(status_code=404, detail="Object not found")
    return _serialize(obj)


@router.get("/{key}/links")
async def get_object_links(key: str, pool: asyncpg.Pool = Depends(get_pool)):
    """Return links with enriched labels from target objects."""
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            """
            SELECT l.type as link_type, l.properties as link_props,
                   o_from.key as from_key, o_from.type as from_type,
                   COALESCE(o_from.properties->>'name', o_from.properties->>'title', o_from.key) as from_label,
                   o_to.key as to_key, o_to.type as to_type,
                   COALESCE(o_to.properties->>'name', o_to.properties->>'title', o_to.key) as to_label
            FROM links l
            JOIN objects o_from ON l.from_id = o_from.id
            JOIN objects o_to ON l.to_id = o_to.id
            WHERE o_from.key = $1 OR o_to.key = $1
            ORDER BY l.type, o_to.key
            LIMIT 200
            """,
            key,
        )
    return [
        {
            "type": r["link_type"],
            "from_key": r["from_key"],
            "from_type": r["from_type"],
            "from_label": r["from_label"],
            "to_key": r["to_key"],
            "to_type": r["to_type"],
            "to_label": r["to_label"],
        }
        for r in rows
    ]


@router.get("/{key}/timeline")
async def get_object_timeline(key: str, pool: asyncpg.Pool = Depends(get_pool)):
    reader = OntologyReader(pool)
    events = await reader.get_timeline(key)
    return [_serialize(e) for e in events]


def _serialize(row: dict) -> dict:
    """Convert asyncpg Record values to JSON-safe types."""
    result = {}
    for k, v in row.items():
        if hasattr(v, "isoformat"):
            result[k] = v.isoformat()
        else:
            result[k] = v
    return result
