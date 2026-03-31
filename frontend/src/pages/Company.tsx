import { useParams, Link } from "react-router-dom";
import { useObject, useObjectLinks, useTimeline } from "@/hooks/useOntology";
import { SourceBadge } from "@/components/SourceBadge";

const YEAR_FIELDS = new Set(["founded", "sic", "rank", "cluster_id"]);
const COUNT_FIELDS = new Set([
  "github_repos", "github_followers", "hf_model_count",
  "hf_total_likes", "hf_total_downloads", "employees",
]);
const MONEY_FIELDS = new Set([
  "market_cap", "revenue", "net_income", "total_assets",
  "cash", "rd_expense", "analyst_target",
]);

function formatValue(key: string, value: unknown): string {
  if (value == null) return "";
  const num = typeof value === "number" ? value : Number(value);

  if (YEAR_FIELDS.has(key) && !isNaN(num))
    return String(Math.round(num));

  if (COUNT_FIELDS.has(key) && !isNaN(num))
    return num.toLocaleString("en-US");

  if (MONEY_FIELDS.has(key) && !isNaN(num)) {
    if (num > 1e12) return `$${(num / 1e12).toFixed(2)}T`;
    if (num > 1e9) return `$${(num / 1e9).toFixed(1)}B`;
    if (num > 1e6) return `$${(num / 1e6).toFixed(1)}M`;
    return `$${num.toLocaleString("en-US")}`;
  }

  if (typeof value === "number") return value.toLocaleString("en-US");
  if (Array.isArray(value)) return value.join(", ");
  return String(value);
}

function PropertyRow({ label, value }: { label: string; value: unknown }) {
  if (value == null || value === "") return null;
  const display = formatValue(label, value);

  return (
    <div className="flex items-center justify-between py-3">
      <span className="text-[10px] font-bold text-secondary uppercase tracking-widest font-label">
        {label.replace(/_/g, " ")}
      </span>
      <span className="text-sm text-on-surface font-medium">{display}</span>
    </div>
  );
}

export function Company() {
  const { key } = useParams<{ key: string }>();
  const { data: obj, isLoading, error } = useObject(key ?? "");
  const { data: links } = useObjectLinks(key ?? "");
  const { data: timeline } = useTimeline(key ?? "");

  if (isLoading) {
    return (
      <div className="animate-pulse space-y-6">
        <div className="h-12 bg-surface-container-high w-1/2" />
        <div className="h-64 bg-surface-container-high" />
      </div>
    );
  }

  if (error || !obj) {
    return (
      <div className="p-6 border border-red-500/30 bg-red-500/5 text-red-400 text-sm">
        Object not found: {key}
      </div>
    );
  }

  const props = obj.properties as Record<string, unknown>;
  const sources = Object.keys(obj.sources);
  const name = (props.name as string) ?? obj.key;

  return (
    <div>
      {/* Header */}
      <header className="mb-12 border-l-2 border-primary pl-8">
        <div className="flex items-center gap-2 text-primary font-label text-xs font-bold uppercase tracking-[0.2em] mb-4">
          <span className="w-2 h-2 bg-primary rounded-full animate-pulse" />
          {obj.type}
        </div>
        <h2 className="text-5xl font-bold tracking-tighter text-on-surface mb-4 font-headline">
          {name}
        </h2>
        <div className="flex items-center gap-4">
          <div className="flex flex-wrap gap-1">
            {sources.map((s) => (
              <SourceBadge key={s} source={s} />
            ))}
          </div>
          <Link
            to={`/graph/${obj.key}`}
            className="text-[10px] font-label font-bold uppercase tracking-widest text-primary hover:text-primary/70 transition-colors flex items-center gap-1"
          >
            View in Graph
            <span className="material-symbols-outlined text-sm">
              arrow_forward
            </span>
          </Link>
        </div>
      </header>

      <div className="grid grid-cols-12 gap-12">
        {/* Properties */}
        <section className="col-span-12 lg:col-span-8 space-y-8">
          <div className="bg-surface-container/50 backdrop-blur-sm border border-outline p-8">
            <h3 className="text-[10px] uppercase tracking-[0.3em] font-bold text-primary mb-6">
              Properties
            </h3>
            <div className="divide-y divide-outline/30">
              {Object.entries(props)
                .filter(
                  ([k]) => !["missing_sources", "name"].includes(k)
                )
                .map(([k, v]) => (
                  <PropertyRow key={k} label={k} value={v} />
                ))}
            </div>
          </div>

          {/* Timeline */}
          {timeline && timeline.length > 0 && (
            <div className="bg-surface-container/50 backdrop-blur-sm border border-outline p-8">
              <h3 className="text-[10px] uppercase tracking-[0.3em] font-bold text-primary mb-6">
                Timeline
              </h3>
              <div className="space-y-4">
                {timeline.map((event) => (
                  <div
                    key={event.key}
                    className="flex items-start gap-4 py-3"
                  >
                    <span className="material-symbols-outlined text-secondary mt-0.5">
                      event
                    </span>
                    <div>
                      <p className="text-sm font-bold text-on-surface">
                        {(event.properties.title as string) ??
                          (event.properties.form as string) ??
                          event.key}
                      </p>
                      <p className="text-[10px] text-secondary mt-1">
                        {(event.properties.date as string) ?? ""}
                        {event.properties.event_type &&
                          ` · ${event.properties.event_type}`}
                      </p>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </section>

        {/* Links sidebar — grouped by type */}
        <aside className="col-span-12 lg:col-span-4 space-y-6">
          <div className="bg-surface-container/50 backdrop-blur-sm border border-outline p-6">
            <h3 className="text-[10px] uppercase tracking-[0.3em] font-bold text-primary mb-4">
              Connections ({(links as unknown[])?.length ?? 0})
            </h3>
            {links && (links as unknown[]).length > 0 ? (
              (() => {
                const grouped: Record<string, Array<Record<string, unknown>>> = {};
                for (const l of links as Array<Record<string, unknown>>) {
                  const t = (l.type as string) || "unknown";
                  (grouped[t] ??= []).push(l);
                }
                return Object.entries(grouped).map(([linkType, items]) => (
                  <div key={linkType} className="mb-5">
                    <p className="text-[9px] text-secondary uppercase tracking-widest font-label mb-2">
                      {linkType.replace(/_/g, " ")} ({items.length})
                    </p>
                    <div className="space-y-1">
                      {items.slice(0, 15).map((link, i) => {
                        const isSource = (link.from_key as string) === key;
                        const targetKey = isSource ? (link.to_key as string) : (link.from_key as string);
                        const targetLabel = isSource ? (link.to_label as string) : (link.from_label as string);
                        const targetType = isSource ? (link.to_type as string) : (link.from_type as string);
                        const route = targetType === "company" ? `/company/${targetKey}` : `/graph/${targetKey}`;
                        return (
                          <Link
                            key={i}
                            to={route}
                            className="flex items-center justify-between py-1.5 px-2 -mx-2 hover:bg-surface-container-high/30 transition-colors"
                          >
                            <div className="min-w-0 flex-1">
                              <p className="text-xs text-on-surface truncate">
                                {targetLabel || targetKey}
                              </p>
                            </div>
                            <span className="material-symbols-outlined text-xs text-secondary/30 ml-2">
                              arrow_forward
                            </span>
                          </Link>
                        );
                      })}
                      {items.length > 15 && (
                        <p className="text-[9px] text-secondary/50 pl-2">+{items.length - 15} more</p>
                      )}
                    </div>
                  </div>
                ));
              })()
            ) : (
              <p className="text-xs text-secondary">No connections yet.</p>
            )}
          </div>
        </aside>
      </div>
    </div>
  );
}
