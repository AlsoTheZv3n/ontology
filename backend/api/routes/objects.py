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
    reader = OntologyReader(pool)
    links = await reader.get_links(key)
    return [_serialize(l) for l in links]


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
