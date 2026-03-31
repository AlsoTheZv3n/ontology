"""FastAPI dependency injection helpers."""

from fastapi import Request
import asyncpg
import redis.asyncio as aioredis


def get_pool(request: Request) -> asyncpg.Pool:
    return request.app.state.pool


def get_redis(request: Request) -> aioredis.Redis:
    return request.app.state.redis
