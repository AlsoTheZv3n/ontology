"""Resolve competitor relationships between companies."""

from __future__ import annotations

import logging

import asyncpg

from store.writer import OntologyWriter

logger = logging.getLogger(__name__)

COMPETITOR_CLUSTERS = [
    {"amazon", "google", "microsoft", "oracle", "ibm", "salesforce", "snowflake", "databricks"},
    {"apple", "microsoft", "google", "meta", "amazon"},
    {"meta", "zoom", "twilio", "spotify"},
    {"crowdstrike", "palo alto networks", "fortinet", "cisco", "elastic"},
    {"gitlab", "atlassian", "hashicorp", "vercel", "supabase", "jetbrains"},
    {"openai", "anthropic", "google", "mistral", "cohere", "hugging face"},
    {"stripe", "paypal", "block", "plaid", "shopify"},
    {"snowflake", "databricks", "mongodb", "elastic", "palantir"},
    {"shopify", "amazon", "doordash", "uber"},
    {"netflix", "spotify", "apple", "amazon"},
    {"nvidia", "amd", "intel", "broadcom", "qualcomm"},
]


async def resolve_competitors(pool: asyncpg.Pool) -> int:
    """Create competitor_of links from SIC codes, sectors, and industry clusters."""
    writer = OntologyWriter(pool)
    created = 0

    async with pool.acquire() as conn:
        sic_rows = await conn.fetch(
            """
            SELECT a.id as id_a, a.key as key_a,
                   b.id as id_b, b.key as key_b,
                   COALESCE(a.properties->>'sic_description', a.properties->>'sector') as sector
            FROM objects a
            JOIN objects b ON
                (a.properties->>'sic' = b.properties->>'sic'
                 OR a.properties->>'sector' = b.properties->>'sector')
                AND a.key < b.key
            WHERE a.type = 'company' AND b.type = 'company'
              AND (a.properties->>'sic' IS NOT NULL OR a.properties->>'sector' IS NOT NULL)
            """
        )

        all_companies = await conn.fetch(
            "SELECT id, key FROM objects WHERE type = 'company'"
        )

    id_by_key = {r["key"]: str(r["id"]) for r in all_companies}

    for row in sic_rows:
        result = await writer.upsert_link(
            "competitor_of", str(row["id_a"]), str(row["id_b"]),
            properties={"sector": row["sector"], "method": "sic_sector"},
        )
        if result:
            created += 1

    for cluster in COMPETITOR_CLUSTERS:
        keys = sorted(cluster & id_by_key.keys())
        for i, key_a in enumerate(keys):
            for key_b in keys[i + 1:]:
                result = await writer.upsert_link(
                    "competitor_of", id_by_key[key_a], id_by_key[key_b],
                    properties={"method": "industry_cluster"},
                )
                if result:
                    created += 1

    logger.info("Created %d competitor links", created)
    return created
