const BASE = "/api";

async function fetchJson<T>(path: string): Promise<T> {
  const res = await fetch(`${BASE}${path}`);
  if (!res.ok) throw new Error(`API error: ${res.status} ${res.statusText}`);
  return res.json();
}

export interface OntologyObject {
  id: string;
  type: string;
  key: string;
  properties: Record<string, unknown>;
  sources: Record<string, unknown>;
  created_at: string;
  updated_at: string;
}

export interface ObjectListResponse {
  items: OntologyObject[];
  total: number;
}

export interface GraphResponse {
  nodes: { id: string; type: string; data: Record<string, unknown> }[];
  edges: { id: string; source: string; target: string; label: string }[];
}

export interface StatsResponse {
  object_counts: Record<string, number>;
  total_links: number;
  total_snapshots: number;
}

export interface Anomaly {
  key: string;
  name: string | null;
  missing_sources: string[];
  source_coverage: number;
}

export const api = {
  listObjects: (params?: { type?: string; missing?: string; limit?: number; offset?: number }) => {
    const qs = new URLSearchParams();
    if (params?.type) qs.set("type", params.type);
    if (params?.missing) qs.set("missing", params.missing);
    if (params?.limit) qs.set("limit", String(params.limit));
    if (params?.offset) qs.set("offset", String(params.offset));
    return fetchJson<ObjectListResponse>(`/objects?${qs}`);
  },

  getObject: (key: string) => fetchJson<OntologyObject>(`/objects/${key}`),

  getLinks: (key: string) => fetchJson<unknown[]>(`/objects/${key}/links`),

  getTimeline: (key: string) => fetchJson<OntologyObject[]>(`/objects/${key}/timeline`),

  getGraph: (root: string, depth = 2) =>
    fetchJson<GraphResponse>(`/graph?root=${root}&depth=${depth}`),

  search: (q: string, type?: string) => {
    const qs = new URLSearchParams({ q });
    if (type) qs.set("type", type);
    return fetchJson<OntologyObject[]>(`/search?${qs}`);
  },

  getStats: () => fetchJson<StatsResponse>("/insights/stats"),

  getAnomalies: () => fetchJson<Anomaly[]>("/insights/anomalies"),

  getTop: (metric: string, limit = 10) =>
    fetchJson<{ key: string; name: string; value: number }[]>(
      `/insights/top?metric=${metric}&limit=${limit}`
    ),

  getTrending: () =>
    fetchJson<{ key: string; name: string; mentions: number }[]>("/insights/trending"),

  getMovers: () =>
    fetchJson<{ key: string; name: string; score: string; updated: string }[]>(
      "/insights/movers"
    ),

  suggest: (q: string) =>
    fetchJson<{ key: string; type: string; name: string }[]>(
      `/search/suggest?q=${encodeURIComponent(q)}`
    ),

  triggerSync: (source: string) =>
    fetch(`${BASE}/sync/${source}`, { method: "POST" }).then((r) => r.json()),
};
