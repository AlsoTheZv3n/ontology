"""Resolve competitor relationships between companies in the same sector."""

from __future__ import annotations

import logging

import asyncpg

from store.writer import OntologyWriter

logger = logging.getLogger(__name__)


async def resolve_competitors(pool: asyncpg.Pool) -> int:
    """Create competitor_of links between Companies sharing the same SIC code or sector."""
    writer = OntologyWriter(pool)
    created = 0

    async with pool.acquire() as conn:
        # Match by SIC code (SEC data)
        rows = await conn.fetch(
            """
            SELECT a.id as id_a, a.key as key_a,
                   b.id as id_b, b.key as key_b,
                   COALESCE(a.properties->>'sic_description', a.properties->>'sector') as sector
            FROM objects a
            JOIN objects b ON
                (
                    (a.properties->>'sic' IS NOT NULL AND a.properties->>'sic' = b.properties->>'sic')
                    OR
                    (a.properties->>'sector' IS NOT NULL AND a.properties->>'sector' = b.properties->>'sector')
                )
                AND a.key < b.key
            WHERE a.type = 'company'
              AND b.type = 'company'
            """
        )

    for row in rows:
        result = await writer.upsert_link(
            "competitor_of",
            str(row["id_a"]),
            str(row["id_b"]),
            properties={"sector": row["sector"]},
        )
        if result:
            created += 1

    logger.info("Created %d competitor links", created)
    return created
