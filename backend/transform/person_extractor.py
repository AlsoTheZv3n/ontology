"""Extract Person objects from existing Company properties and Events."""

from __future__ import annotations

import json
import logging
import re

import asyncpg

from store.writer import OntologyWriter
from schemas.objects import PersonObject

logger = logging.getLogger(__name__)


def _canonical_person_key(name: str) -> str:
    """'Tim Cook' → 'tim-cook'"""
    return re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")


async def extract_ceos(pool: asyncpg.Pool) -> int:
    """Read all Companies with 'ceo' property and create Person objects + is_ceo_of links."""
    writer = OntologyWriter(pool)
    created = 0

    async with pool.acquire() as conn:
        rows = await conn.fetch(
            """
            SELECT id, key, properties->>'name' as company_name,
                   properties->>'ceo' as ceo_name
            FROM objects
            WHERE type = 'company'
              AND properties->>'ceo' IS NOT NULL
              AND length(properties->>'ceo') > 2
            """
        )

    for row in rows:
        ceo_name = str(row["ceo_name"]).strip()
        company_key = row["key"]
        company_id = str(row["id"])

        person_key = _canonical_person_key(ceo_name)
        if not person_key or len(person_key) < 2:
            continue

        obj = PersonObject(
            key=person_key,
            properties={
                "name": ceo_name,
                "role": "CEO",
                "company_key": company_key,
            },
            sources={"derived": {"from": "company_ceo_property", "company": company_key}},
        )
        person_id = await writer.upsert(obj)
        await writer.upsert_link("is_ceo_of", person_id, company_id)
        created += 1

    logger.info("Extracted %d CEOs", created)
    return created


async def extract_patent_inventors(pool: asyncpg.Pool) -> int:
    """Read Patent events and create Person objects for inventors."""
    writer = OntologyWriter(pool)
    created = 0

    async with pool.acquire() as conn:
        rows = await conn.fetch(
            """
            SELECT e.id as event_id, e.key as event_key,
                   e.properties as event_props
            FROM objects e
            WHERE e.type = 'event'
              AND e.properties->>'event_type' = 'patent'
            """
        )

    for row in rows:
        props = row["event_props"]
        if not isinstance(props, dict):
            try:
                props = json.loads(props)
            except Exception:
                continue

        # PatentsView stores inventors as separate first/last name fields in sources
        sources = {}
        patent_src = props.get("sources", {})
        if isinstance(patent_src, dict):
            sources = patent_src

        # Try to get inventor from the event properties
        inventor_first = props.get("inventor_first_name", "")
        inventor_last = props.get("inventor_last_name", "")
        if inventor_first and inventor_last:
            full_name = f"{inventor_first} {inventor_last}".strip()
        else:
            continue

        if len(full_name) < 3:
            continue

        person_key = _canonical_person_key(full_name)
        obj = PersonObject(
            key=person_key,
            properties={
                "name": full_name,
                "role": "Inventor",
            },
            sources={"patents": {"event_key": row["event_key"]}},
        )
        person_id = await writer.upsert(obj)
        await writer.upsert_link("invented", person_id, str(row["event_id"]))
        created += 1

    logger.info("Extracted %d patent inventors", created)
    return created
