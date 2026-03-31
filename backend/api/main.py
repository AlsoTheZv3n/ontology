from contextlib import asynccontextmanager
import json

import asyncpg
import redis.asyncio as aioredis
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.routes import chat, graph, insights, objects, search, sync
from config import settings


async def _init_connection(conn: asyncpg.Connection):
    """Register JSONB codec so asyncpg returns dicts instead of strings."""
    await conn.set_type_codec(
        "jsonb",
        encoder=json.dumps,
        decoder=json.loads,
        schema="pg_catalog",
    )
    await conn.set_type_codec(
        "json",
        encoder=json.dumps,
        decoder=json.loads,
        schema="pg_catalog",
    )


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.pool = await asyncpg.create_pool(
        settings.database_url,
        init=_init_connection,
    )
    app.state.redis = aioredis.from_url(settings.redis_url)
    yield
    await app.state.pool.close()
    await app.state.redis.close()


app = FastAPI(
    title="Ontology API",
    version="1.0.0",
    description="Tech Company Ontology — unified object graph from 7 public data sources",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:5174"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(objects.router, prefix="/objects", tags=["Objects"])
app.include_router(graph.router, prefix="/graph", tags=["Graph"])
app.include_router(search.router, prefix="/search", tags=["Search"])
app.include_router(insights.router, prefix="/insights", tags=["Insights"])
app.include_router(sync.router, prefix="/sync", tags=["Sync"])
app.include_router(chat.router, prefix="/chat", tags=["Chat"])


@app.get("/health")
async def health():
    return {"status": "ok"}
