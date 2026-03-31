import { useEffect, useState } from "react";
import { Link } from "react-router-dom";

interface EntityItem {
  name: string;
  key: string;
  type: string;
  sources: Record<string, unknown> | string[];
  updated_at: string;
}

interface StatsResponse {
  object_counts: Record<string, number>;
}

const ENTITY_TYPES = [
  "company",
  "person",
  "article",
  "repository",
  "event",
  "macro_indicator",
  "country",
  "paper",
] as const;

const TYPE_COLORS: Record<string, string> = {
  company: "bg-indigo-500/20 text-indigo-400 border-indigo-500/30",
  person: "bg-sky-500/20 text-sky-400 border-sky-500/30",
  article: "bg-orange-500/20 text-orange-400 border-orange-500/30",
  repository: "bg-emerald-500/20 text-emerald-400 border-emerald-500/30",
  event: "bg-purple-500/20 text-purple-400 border-purple-500/30",
  macro_indicator: "bg-teal-500/20 text-teal-400 border-teal-500/30",
  country: "bg-amber-500/20 text-amber-400 border-amber-500/30",
  paper: "bg-rose-500/20 text-rose-400 border-rose-500/30",
};

function SourceBadge({ source }: { source: string }) {
  return (
    <span className="text-[9px] font-label font-bold uppercase tracking-widest text-secondary bg-surface-container-high px-1.5 py-0.5 border border-outline">
      {source}
    </span>
  );
}

function timeAgo(dateStr: string): string {
  const now = Date.now();
  const then = new Date(dateStr).getTime();
  const diff = now - then;
  const mins = Math.floor(diff / 60000);
  if (mins < 60) return `${mins}m ago`;
  const hours = Math.floor(mins / 60);
  if (hours < 24) return `${hours}h ago`;
  const days = Math.floor(hours / 24);
  return `${days}d ago`;
}

export function Entities() {
  const [counts, setCounts] = useState<Record<string, number>>({});
  const [selected, setSelected] = useState<string>("company");
  const [entities, setEntities] = useState<EntityItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [listLoading, setListLoading] = useState(false);

  // Fetch stats for counts
  useEffect(() => {
    fetch("/api/insights/stats")
      .then((r) => r.json())
      .then((d: StatsResponse) => {
        setCounts(d.object_counts ?? {});
        setLoading(false);
      })
      .catch(() => setLoading(false));
  }, []);

  // Fetch entities when selected type changes
  useEffect(() => {
    setListLoading(true);
    fetch(`/api/insights/entities?type=${selected}&limit=50`)
      .then((r) => r.json())
      .then((d) => {
        setEntities(Array.isArray(d) ? d : d.items ?? []);
        setListLoading(false);
      })
      .catch(() => {
        setEntities([]);
        setListLoading(false);
      });
  }, [selected]);

  function entityLink(entity: EntityItem): string {
    if (entity.type === "company") return `/company/${entity.key}`;
    return `/graph/${entity.key}`;
  }

  function renderSources(sources: Record<string, unknown> | string[]): React.ReactNode {
    const keys = Array.isArray(sources) ? sources : Object.keys(sources ?? {});
    if (keys.length === 0) return <span className="text-xs text-secondary">—</span>;
    return (
      <div className="flex flex-wrap gap-1">
        {keys.map((s) => (
          <SourceBadge key={String(s)} source={String(s)} />
        ))}
      </div>
    );
  }

  return (
    <div>
      {/* Header */}
      <header className="mb-12 border-l-2 border-primary pl-8">
        <div className="flex items-center gap-2 text-primary font-label text-xs font-bold uppercase tracking-[0.2em] mb-4">
          <span className="w-2 h-2 bg-primary rounded-full animate-pulse" />
          Knowledge Graph
        </div>
        <h2 className="text-5xl font-bold tracking-tighter text-on-surface mb-4 font-headline">
          Entity Browser
        </h2>
        <p className="text-on-surface-variant max-w-2xl text-lg font-light leading-relaxed">
          Browse all tracked entities by type. Click any row to explore its graph.
        </p>
      </header>

      {/* Type Chips */}
      <div className="flex flex-wrap gap-2 mb-8">
        {ENTITY_TYPES.map((t) => {
          const isActive = selected === t;
          const count = counts[t] ?? 0;
          return (
            <button
              key={t}
              onClick={() => setSelected(t)}
              className={`px-4 py-2 text-[10px] font-label font-bold uppercase tracking-widest border transition-all ${
                isActive
                  ? TYPE_COLORS[t] ?? "bg-primary/20 text-primary border-primary/30"
                  : "bg-surface-container/50 text-secondary border-outline hover:border-primary/30 hover:text-on-surface"
              }`}
            >
              {t.replace("_", " ")}
              <span className="ml-2 opacity-70">{loading ? "..." : count}</span>
            </button>
          );
        })}
      </div>

      {/* Entity Table */}
      {listLoading ? (
        <p className="text-sm text-secondary font-label">Loading entities...</p>
      ) : entities.length === 0 ? (
        <div className="bg-surface-container/50 border border-outline p-8 text-center">
          <p className="text-sm text-secondary">
            No {selected.replace("_", " ")} entities found.
          </p>
        </div>
      ) : (
        <div className="bg-surface-container/50 border border-outline overflow-hidden">
          <table className="w-full">
            <thead>
              <tr className="border-b border-outline">
                <th className="text-left text-[10px] font-label font-bold uppercase tracking-widest text-secondary px-4 py-3">
                  Name
                </th>
                <th className="text-left text-[10px] font-label font-bold uppercase tracking-widest text-secondary px-4 py-3">
                  Key
                </th>
                <th className="text-left text-[10px] font-label font-bold uppercase tracking-widest text-secondary px-4 py-3">
                  Sources
                </th>
                <th className="text-right text-[10px] font-label font-bold uppercase tracking-widest text-secondary px-4 py-3">
                  Updated
                </th>
              </tr>
            </thead>
            <tbody>
              {entities.map((entity) => (
                <tr
                  key={entity.key}
                  className="border-b border-outline/50 hover:bg-surface-container-high/30 transition-colors"
                >
                  <td className="px-4 py-3">
                    <Link
                      to={entityLink(entity)}
                      className="text-sm text-on-surface font-medium hover:text-primary transition-colors"
                    >
                      {entity.name || entity.key}
                    </Link>
                  </td>
                  <td className="px-4 py-3 text-xs text-secondary font-mono">
                    {entity.key}
                  </td>
                  <td className="px-4 py-3">
                    {renderSources(entity.sources)}
                  </td>
                  <td className="px-4 py-3 text-xs text-on-surface-variant text-right">
                    {entity.updated_at ? timeAgo(entity.updated_at) : "—"}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
