"""ARQ worker configuration."""

from __future__ import annotations

import asyncpg
import redis.asyncio as aioredis
from arq import cron
from arq.connections import RedisSettings

from config import settings
from jobs.tasks import (
    build_competitor_links,
    compute_derived,
    extract_persons,
    resolve_entities,
    sync_eia,
    sync_forbes,
    sync_fred,
    sync_github,
    sync_hn,
    sync_hn_algolia,
    sync_huggingface,
    sync_patents,
    sync_sec,
    sync_countries,
    sync_sec_financials,
    sync_semantic_scholar,
    sync_wikidata,
    sync_wikipedia,
    sync_world_bank_macro,
    sync_yahoo_finance,
)


async def startup(ctx: dict) -> None:
    ctx["pool"] = await asyncpg.create_pool(settings.database_url)
    ctx["redis"] = aioredis.from_url(settings.redis_url)
    ctx["github_token"] = settings.github_token
    ctx["sec_user_agent"] = settings.sec_user_agent


async def shutdown(ctx: dict) -> None:
    await ctx["pool"].close()
    await ctx["redis"].close()


class WorkerSettings:
    redis_settings = RedisSettings.from_dsn(settings.redis_url)
    functions = [
        sync_wikipedia,
        sync_github,
        sync_yahoo_finance,
        sync_hn,
        sync_hn_algolia,
        sync_huggingface,
        sync_sec,
        sync_patents,
        sync_forbes,
        sync_fred,
        sync_eia,
        compute_derived,
        resolve_entities,
        extract_persons,
        build_competitor_links,
        sync_wikidata,
        sync_sec_financials,
        sync_countries,
        sync_world_bank_macro,
        sync_semantic_scholar,
    ]
    cron_jobs = [
        cron(sync_wikipedia, hour=2, minute=0),
        cron(sync_github, hour=2, minute=30),
        cron(sync_yahoo_finance, hour=8, minute=0),
        cron(sync_hn, minute={0, 30}),
        cron(sync_huggingface, hour=3, minute=0),
        cron(sync_sec, weekday=0, hour=3),
        cron(sync_patents, weekday=1, hour=3),
        cron(sync_fred, hour={6, 12, 18, 0}),
        cron(sync_eia, hour={6, 18}),
        cron(compute_derived, hour={6, 12, 18}),
        cron(extract_persons, hour=4, minute=0),
        cron(build_competitor_links, hour=4, minute=30),
        cron(sync_wikidata, hour=1, minute=0),
        cron(sync_sec_financials, weekday=1, hour=3, minute=30),
        cron(sync_countries, weekday=0, hour=4),
        cron(sync_world_bank_macro, hour=5, minute=0),
        cron(sync_semantic_scholar, hour=3, minute=0),
    ]
    on_startup = startup
    on_shutdown = shutdown
