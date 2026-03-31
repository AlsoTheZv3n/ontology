"""Graph endpoint — returns nodes and edges for React Flow."""

from __future__ import annotations

from fastapi import APIRouter, Depends
import asyncpg

from api.deps import get_pool
from store.reader import OntologyReader

router = APIRouter()


@router.get("")
async def get_graph(
    root: str,
    depth: int = 2,
    pool: asyncpg.Pool = Depends(get_pool),
):
    reader = OntologyReader(pool)
    return await reader.get_graph(root, depth=min(depth, 4))
