-- Extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS vector;

-- Core: Object Store
CREATE TABLE objects (
    id          UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    type        TEXT NOT NULL,
    key         TEXT NOT NULL,
    properties  JSONB NOT NULL DEFAULT '{}',
    sources     JSONB NOT NULL DEFAULT '{}',
    embedding   vector(1536),
    created_at  TIMESTAMPTZ DEFAULT now(),
    updated_at  TIMESTAMPTZ DEFAULT now(),
    UNIQUE (type, key)
);

-- Core: Link Store (Graph Edges)
CREATE TABLE links (
    id          UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    type        TEXT NOT NULL,
    from_id     UUID NOT NULL REFERENCES objects(id) ON DELETE CASCADE,
    to_id       UUID NOT NULL REFERENCES objects(id) ON DELETE CASCADE,
    weight      FLOAT DEFAULT 1.0,
    properties  JSONB DEFAULT '{}',
    created_at  TIMESTAMPTZ DEFAULT now(),
    UNIQUE (type, from_id, to_id)
);

-- Raw Snapshots (unmodified API responses)
CREATE TABLE raw_snapshots (
    id          UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    source      TEXT NOT NULL,
    entity_key  TEXT NOT NULL,
    payload     JSONB NOT NULL,
    fetched_at  TIMESTAMPTZ DEFAULT now()
);

-- Performance indexes
CREATE INDEX idx_objects_type ON objects (type);
CREATE INDEX idx_objects_properties ON objects USING GIN (properties);
CREATE INDEX idx_objects_sources ON objects USING GIN (sources);
CREATE INDEX idx_links_from ON links (from_id);
CREATE INDEX idx_links_to ON links (to_id);
CREATE INDEX idx_links_type_from ON links (type, from_id);
CREATE INDEX idx_raw_source_key ON raw_snapshots (source, entity_key);

-- Materialized View: Company Insights
CREATE MATERIALIZED VIEW company_insights AS
SELECT
    o.id,
    o.key,
    o.properties->>'name'                              AS name,
    o.properties->>'sector'                            AS sector,
    (o.properties->>'market_cap')::float               AS market_cap,
    (o.properties->>'github_stars')::int               AS github_stars,
    (o.properties->>'innovation_score')::float         AS innovation_score,
    COALESCE(jsonb_array_length(o.properties->'missing_sources'), 0) AS missing_source_count,
    COUNT(DISTINCT l.id) FILTER (WHERE l.type = 'mentions')  AS article_mentions,
    COUNT(DISTINCT l.id) FILTER (WHERE l.type = 'owns_repo') AS repo_count
FROM objects o
LEFT JOIN links l ON l.to_id = o.id
WHERE o.type = 'company'
GROUP BY o.id, o.key, o.properties;

CREATE UNIQUE INDEX ON company_insights (id);
