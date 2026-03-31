import { Dispatch, SetStateAction } from "react";

export interface GraphFilters {
  nodeTypes: Set<string>;
  linkTypes: Set<string>;
  layout: "dagre-lr" | "dagre-tb" | "radial";
  showLabels: boolean;
}

export const ALL_NODE_TYPES = ["company", "article", "repository", "event", "person"];
export const ALL_LINK_TYPES = ["mentions", "owns_repo", "filed", "is_ceo_of", "contributed_to", "competitor_of"];

const NODE_COLORS: Record<string, string> = {
  company: "bg-blue-500",
  article: "bg-orange-500",
  repository: "bg-emerald-500",
  event: "bg-purple-500",
  person: "bg-sky-500",
};

const NODE_ICONS: Record<string, string> = {
  company: "domain",
  article: "article",
  repository: "code",
  event: "event",
  person: "person",
};

interface Props {
  filters: GraphFilters;
  setFilters: Dispatch<SetStateAction<GraphFilters>>;
  stats?: { nodes: number; edges: number; byType: Record<string, number> };
}

export function GraphFilterPanel({ filters, setFilters, stats }: Props) {
  const toggleNode = (type: string) => {
    setFilters((f) => {
      const next = new Set(f.nodeTypes);
      next.has(type) ? next.delete(type) : next.add(type);
      return { ...f, nodeTypes: next };
    });
  };

  const toggleLink = (type: string) => {
    setFilters((f) => {
      const next = new Set(f.linkTypes);
      next.has(type) ? next.delete(type) : next.add(type);
      return { ...f, linkTypes: next };
    });
  };

  const selectAll = () => {
    setFilters((f) => ({
      ...f,
      nodeTypes: new Set(ALL_NODE_TYPES),
      linkTypes: new Set(ALL_LINK_TYPES),
    }));
  };

  const reset = () => {
    setFilters({
      nodeTypes: new Set(ALL_NODE_TYPES),
      linkTypes: new Set(ALL_LINK_TYPES),
      layout: "dagre-lr",
      showLabels: true,
    });
  };

  return (
    <div className="w-64 flex-shrink-0 bg-surface-container/50 backdrop-blur-sm border border-outline p-5 space-y-6 overflow-y-auto max-h-[calc(100vh-12rem)]">
      {/* Header */}
      <div className="flex items-center justify-between">
        <h3 className="text-[10px] uppercase tracking-[0.3em] font-bold text-primary font-label">
          Filters
        </h3>
        <div className="flex gap-2">
          <button
            onClick={selectAll}
            className="text-[9px] text-secondary hover:text-on-surface uppercase tracking-widest font-label transition-colors"
          >
            All
          </button>
          <button
            onClick={reset}
            className="text-[9px] text-secondary hover:text-on-surface uppercase tracking-widest font-label transition-colors"
          >
            Reset
          </button>
        </div>
      </div>

      {/* Node Types */}
      <div>
        <p className="text-[10px] font-bold text-secondary uppercase tracking-widest mb-3 font-label">
          Node Types
        </p>
        <div className="space-y-1.5">
          {ALL_NODE_TYPES.map((type) => (
            <button
              key={type}
              onClick={() => toggleNode(type)}
              className={`w-full flex items-center gap-2.5 px-3 py-2 text-left transition-all ${
                filters.nodeTypes.has(type)
                  ? "text-on-surface"
                  : "text-secondary/40"
              }`}
            >
              <span
                className={`w-2.5 h-2.5 rounded-full transition-opacity ${NODE_COLORS[type]} ${
                  filters.nodeTypes.has(type) ? "opacity-100" : "opacity-20"
                }`}
              />
              <span className="material-symbols-outlined text-sm">
                {NODE_ICONS[type]}
              </span>
              <span className="text-xs font-medium flex-1 capitalize">
                {type}
              </span>
              {stats?.byType[type] !== undefined && (
                <span className="text-[10px] text-secondary font-label">
                  {stats.byType[type]}
                </span>
              )}
            </button>
          ))}
        </div>
      </div>

      {/* Link Types */}
      <div>
        <p className="text-[10px] font-bold text-secondary uppercase tracking-widest mb-3 font-label">
          Connections
        </p>
        <div className="space-y-1.5">
          {ALL_LINK_TYPES.map((type) => (
            <button
              key={type}
              onClick={() => toggleLink(type)}
              className={`w-full flex items-center gap-2.5 px-3 py-2 text-left transition-all ${
                filters.linkTypes.has(type)
                  ? "text-on-surface"
                  : "text-secondary/40"
              }`}
            >
              <span
                className={`w-4 h-0.5 transition-opacity ${
                  filters.linkTypes.has(type)
                    ? "bg-primary opacity-100"
                    : "bg-secondary opacity-20"
                }`}
              />
              <span className="text-xs font-medium flex-1">
                {type.replace(/_/g, " ")}
              </span>
            </button>
          ))}
        </div>
      </div>

      {/* Layout */}
      <div>
        <p className="text-[10px] font-bold text-secondary uppercase tracking-widest mb-3 font-label">
          Layout
        </p>
        <div className="space-y-1">
          {[
            { key: "dagre-lr" as const, label: "Horizontal", icon: "arrow_forward" },
            { key: "dagre-tb" as const, label: "Vertical", icon: "arrow_downward" },
            { key: "radial" as const, label: "Radial", icon: "blur_circular" },
          ].map((opt) => (
            <button
              key={opt.key}
              onClick={() => setFilters((f) => ({ ...f, layout: opt.key }))}
              className={`w-full flex items-center gap-2.5 px-3 py-2 text-left transition-all ${
                filters.layout === opt.key
                  ? "bg-primary/10 text-primary border border-primary/20"
                  : "text-secondary hover:text-on-surface"
              }`}
            >
              <span className="material-symbols-outlined text-sm">
                {opt.icon}
              </span>
              <span className="text-xs font-medium">{opt.label}</span>
            </button>
          ))}
        </div>
      </div>

      {/* Show labels */}
      <div className="flex items-center justify-between px-3">
        <span className="text-xs text-secondary">Edge Labels</span>
        <button
          onClick={() =>
            setFilters((f) => ({ ...f, showLabels: !f.showLabels }))
          }
          className={`w-8 h-4 rounded-full relative transition-colors ${
            filters.showLabels ? "bg-primary" : "bg-secondary/30"
          }`}
        >
          <span
            className={`absolute top-0.5 w-3 h-3 rounded-full bg-surface transition-all ${
              filters.showLabels ? "right-0.5" : "left-0.5"
            }`}
          />
        </button>
      </div>

      {/* Stats */}
      {stats && (
        <div className="border-t border-outline/30 pt-4">
          <div className="flex justify-between text-[10px] text-secondary font-label uppercase tracking-widest">
            <span>{stats.nodes} nodes</span>
            <span>{stats.edges} edges</span>
          </div>
        </div>
      )}
    </div>
  );
}

export function defaultFilters(): GraphFilters {
  return {
    nodeTypes: new Set(ALL_NODE_TYPES),
    linkTypes: new Set(ALL_LINK_TYPES),
    layout: "dagre-lr",
    showLabels: true,
  };
}
