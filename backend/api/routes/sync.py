"""Sync endpoints — manually trigger data source sync jobs."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException
from arq.connections import create_pool, RedisSettings

from config import settings

router = APIRouter()

VALID_SOURCES = [
    "wikipedia", "github", "yahoo_finance", "hn", "hn_algolia",
    "huggingface", "sec", "patents", "forbes", "fred", "eia", "derived", "resolve",
]

TASK_MAP = {
    "wikipedia": "sync_wikipedia",
    "github": "sync_github",
    "yahoo_finance": "sync_yahoo_finance",
    "hn": "sync_hn",
    "hn_algolia": "sync_hn_algolia",
    "huggingface": "sync_huggingface",
    "sec": "sync_sec",
    "patents": "sync_patents",
    "forbes": "sync_forbes",
    "fred": "sync_fred",
    "eia": "sync_eia",
    "derived": "compute_derived",
    "resolve": "resolve_entities",
}


@router.post("/{source}")
async def trigger_sync(source: str):
    if source not in VALID_SOURCES:
        raise HTTPException(
            status_code=400,
            detail=f"Unknown source '{source}'. Valid: {VALID_SOURCES}",
        )

    redis_settings = RedisSettings.from_dsn(settings.redis_url)
    pool = await create_pool(redis_settings)
    await pool.enqueue_job(TASK_MAP[source])
    await pool.close()

    return {"status": "queued", "source": source}


@router.get("/sources")
async def list_sources():
    return {"sources": VALID_SOURCES}
