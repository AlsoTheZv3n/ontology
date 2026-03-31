"""Write/upsert objects and links into PostgreSQL."""

from __future__ import annotations

import json

import asyncpg

from schemas.objects import OntologyObject


def _ensure_dict(val) -> dict:
    """Ensure value is a dict (handles str from bad codec state)."""
    if isinstance(val, dict):
        return val
    if isinstance(val, str):
        try:
            return json.loads(val)
        except (json.JSONDecodeError, TypeError):
            return {}
    return {}


class OntologyWriter:
    def __init__(self, pool: asyncpg.Pool):
        self.pool = pool

    async def upsert(self, obj: OntologyObject) -> str:
        """Upsert an object. Properties and sources are shallow-merged. Returns UUID."""
        props = _ensure_dict(obj.properties)
        srcs = _ensure_dict(obj.sources)
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                INSERT INTO objects (type, key, properties, sources)
                VALUES ($1, $2, $3::jsonb, $4::jsonb)
                ON CONFLICT (type, key) DO UPDATE SET
                    properties = objects.properties || EXCLUDED.properties,
                    sources    = objects.sources    || EXCLUDED.sources,
                    updated_at = now()
                RETURNING id
                """,
                obj.type,
                obj.key,
                json.dumps(props),
                json.dumps(srcs),
            )
            return str(row["id"])

    async def upsert_link(
        self,
        link_type: str,
        from_id: str,
        to_id: str,
        weight: float = 1.0,
        properties: dict | None = None,
    ) -> str | None:
        """Create or ignore a link. Returns UUID or None on conflict."""
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                INSERT INTO links (type, from_id, to_id, weight, properties)
                VALUES ($1, $2::uuid, $3::uuid, $4, $5::jsonb)
                ON CONFLICT (type, from_id, to_id) DO NOTHING
                RETURNING id
                """,
                link_type,
                from_id,
                to_id,
                weight,
                json.dumps(properties or {}),
            )
            return str(row["id"]) if row else None

    async def save_raw_snapshot(
        self, source: str, entity_key: str, payload: dict
    ) -> str:
        """Archive a raw API response."""
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                INSERT INTO raw_snapshots (source, entity_key, payload)
                VALUES ($1, $2, $3::jsonb)
                RETURNING id
                """,
                source,
                entity_key,
                json.dumps(_ensure_dict(payload)),
            )
            return str(row["id"])

    async def get_id(self, obj_type: str, key: str) -> str | None:
        """Look up an object's UUID by type and key."""
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT id FROM objects WHERE type = $1 AND key = $2",
                obj_type,
                key,
            )
            return str(row["id"]) if row else None
