"""ARQ worker configuration."""

from __future__ import annotations

import asyncpg
import redis.asyncio as aioredis
from arq import cron
from arq.connections import RedisSettings

from config import settings
from jobs.tasks import (
    compute_derived,
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
    sync_wikipedia,
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
    ]
    on_startup = startup
    on_shutdown = shutdown
