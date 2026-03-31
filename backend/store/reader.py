"""Read objects, links, and graphs from PostgreSQL."""

from __future__ import annotations

import asyncpg


def _node_label(obj_type: str, props: dict, key: str) -> str:
    """Build a human-readable label for any object type."""
    if obj_type == "event":
        form = props.get("form", "")
        date = str(props.get("date", ""))[:10]
        if form and date:
            return f"{form} — {date}"
        if form:
            return form
        return f"Event {date}" if date else key

    return props.get("name") or props.get("title") or key


class OntologyReader:
    def __init__(self, pool: asyncpg.Pool):
        self.pool = pool

    async def get_object(self, key: str) -> dict | None:
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT * FROM objects WHERE key = $1", key
            )
            return dict(row) if row else None

    async def list_objects(
        self,
        obj_type: str | None = None,
        missing_source: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[dict], int]:
        """List objects with optional type / missing-source filter."""
        conditions = []
        params: list = []
        idx = 1

        if obj_type:
            conditions.append(f"type = ${idx}")
            params.append(obj_type)
            idx += 1

        if missing_source:
            conditions.append(f"NOT (sources ? ${idx})")
            params.append(missing_source)
            idx += 1

        where = f"WHERE {' AND '.join(conditions)}" if conditions else ""

        async with self.pool.acquire() as conn:
            count = await conn.fetchval(
                f"SELECT count(*) FROM objects {where}", *params
            )
            rows = await conn.fetch(
                f"SELECT * FROM objects {where} ORDER BY updated_at DESC LIMIT ${idx} OFFSET ${idx + 1}",
                *params,
                limit,
                offset,
            )
            return [dict(r) for r in rows], count

    async def get_links(self, key: str) -> list[dict]:
        """Get all links where the object with the given key is from or to."""
        async with self.pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT l.id, l.type, l.weight, l.properties, l.created_at,
                       o_from.key as from_key, o_from.type as from_type,
                       o_to.key as to_key, o_to.type as to_type
                FROM links l
                JOIN objects o_from ON l.from_id = o_from.id
                JOIN objects o_to ON l.to_id = o_to.id
                WHERE o_from.key = $1 OR o_to.key = $1
                """,
                key,
            )
            return [dict(r) for r in rows]

    async def get_graph(self, root_key: str, depth: int = 2) -> dict:
        """Build a subgraph starting from root_key up to N hops."""
        async with self.pool.acquire() as conn:
            root = await conn.fetchrow(
                "SELECT id, key, type, properties FROM objects WHERE key = $1",
                root_key,
            )
            if not root:
                return {"nodes": [], "edges": []}

            nodes_map: dict[str, dict] = {}
            edges_list: list[dict] = []
            seen_edge_ids: set[str] = set()
            visited_ids: set = set()

            # Seed with root
            root_uuid = root["id"]
            props = root["properties"] if isinstance(root["properties"], dict) else {}
            nodes_map[root["key"]] = {
                "id": root["key"],
                "type": root["type"],
                "data": {"label": _node_label(root["type"], props, root["key"])},
            }

            current_ids = [root_uuid]

            for _ in range(depth):
                if not current_ids:
                    break
                visited_ids.update(current_ids)

                rows = await conn.fetch(
                    """
                    SELECT l.id as link_id, l.type as link_type,
                           o_from.key as from_key, o_from.type as from_type,
                           o_from.properties as from_props,
                           o_to.key as to_key, o_to.type as to_type,
                           o_to.properties as to_props,
                           o_from.id as from_uuid, o_to.id as to_uuid
                    FROM links l
                    JOIN objects o_from ON l.from_id = o_from.id
                    JOIN objects o_to ON l.to_id = o_to.id
                    WHERE l.from_id = ANY($1::uuid[]) OR l.to_id = ANY($1::uuid[])
                    """,
                    current_ids,
                )

                next_ids = []
                for row in rows:
                    link_id = str(row["link_id"])
                    if link_id in seen_edge_ids:
                        continue
                    seen_edge_ids.add(link_id)

                    # Add edge using keys (matching node ids)
                    edges_list.append({
                        "id": link_id,
                        "source": row["from_key"],
                        "target": row["to_key"],
                        "label": row["link_type"],
                    })

                    # Add nodes we haven't seen
                    for side in ("from", "to"):
                        key = row[f"{side}_key"]
                        uuid = row[f"{side}_uuid"]
                        if key not in nodes_map:
                            p = row[f"{side}_props"]
                            p = p if isinstance(p, dict) else {}
                            nodes_map[key] = {
                                "id": key,
                                "type": row[f"{side}_type"],
                                "data": {"label": _node_label(row[f"{side}_type"], p, key)},
                            }
                            if uuid not in visited_ids:
                                next_ids.append(uuid)

                current_ids = next_ids

        return {
            "nodes": list(nodes_map.values()),
            "edges": edges_list,
        }

    async def search(
        self, query: str, obj_type: str | None = None, limit: int = 20
    ) -> list[dict]:
        """Relevance-ranked search across object properties.

        Ranking factors:
        1. Key exact match (highest priority)
        2. Name contains query
        3. Companies ranked above other types
        4. More sources = higher rank
        """
        conditions = ["properties::text ILIKE $1"]
        params: list = [f"%{query}%"]
        idx = 2

        if obj_type:
            conditions.append(f"type = ${idx}")
            params.append(obj_type)
            idx += 1

        where = " AND ".join(conditions)

        async with self.pool.acquire() as conn:
            rows = await conn.fetch(
                f"""SELECT *,
                    (CASE WHEN key = ${idx} THEN 100 ELSE 0 END
                     + CASE WHEN properties->>'name' ILIKE $1 THEN 50 ELSE 0 END
                     + CASE type WHEN 'company' THEN 20 WHEN 'person' THEN 10 ELSE 0 END
                     + COALESCE(jsonb_array_length(
                         CASE WHEN jsonb_typeof(sources) = 'object'
                              THEN (SELECT jsonb_agg(k) FROM jsonb_object_keys(sources) k)
                              ELSE '[]'::jsonb END
                       ), 0) * 5
                    ) as relevance
                FROM objects WHERE {where}
                ORDER BY relevance DESC, updated_at DESC
                LIMIT ${idx + 1}""",
                *params,
                query.lower(),
                limit,
            )
            return [dict(r) for r in rows]

    async def get_timeline(self, key: str) -> list[dict]:
        """Get chronologically sorted events linked to an object."""
        async with self.pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT e.*
                FROM objects e
                JOIN links l ON (l.to_id = e.id OR l.from_id = e.id)
                JOIN objects o ON (o.id = l.from_id OR o.id = l.to_id)
                WHERE o.key = $1 AND e.type = 'event' AND e.id != o.id
                ORDER BY e.properties->>'date' DESC
                """,
                key,
            )
            return [dict(r) for r in rows]

    async def get_similar(self, key: str, limit: int = 5) -> list[dict]:
        """Find similar objects via pgvector cosine similarity."""
        async with self.pool.acquire() as conn:
            obj = await conn.fetchrow(
                "SELECT embedding FROM objects WHERE key = $1", key
            )
            if not obj or obj["embedding"] is None:
                return []

            rows = await conn.fetch(
                """
                SELECT *, embedding <=> $1 AS distance
                FROM objects
                WHERE key != $2 AND embedding IS NOT NULL
                ORDER BY embedding <=> $1
                LIMIT $3
                """,
                obj["embedding"],
                key,
                limit,
            )
            return [dict(r) for r in rows]

    async def get_top_by_metric(
        self, metric: str, limit: int = 10
    ) -> list[dict]:
        """Top companies by a numeric property."""
        async with self.pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT key, properties->>'name' as name,
                       (properties->>$1)::float as value
                FROM objects
                WHERE type = 'company' AND properties ? $1
                ORDER BY (properties->>$1)::float DESC NULLS LAST
                LIMIT $2
                """,
                metric,
                limit,
            )
            return [dict(r) for r in rows]
