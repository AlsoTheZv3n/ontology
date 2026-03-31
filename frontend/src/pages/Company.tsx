import { useParams, Link } from "react-router-dom";
import { useObject, useObjectLinks, useTimeline } from "@/hooks/useOntology";
import { SourceBadge } from "@/components/SourceBadge";

function PropertyRow({ label, value }: { label: string; value: unknown }) {
  if (value == null || value === "") return null;
  const display =
    typeof value === "number"
      ? value.toLocaleString()
      : Array.isArray(value)
        ? value.join(", ")
        : String(value);

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

        {/* Links sidebar */}
        <aside className="col-span-12 lg:col-span-4">
          <div className="bg-surface-container/50 backdrop-blur-sm border border-outline p-8">
            <h3 className="text-[10px] uppercase tracking-[0.3em] font-bold text-primary mb-6">
              Connections ({links?.length ?? 0})
            </h3>
            {links && links.length > 0 ? (
              <div className="space-y-3">
                {(links as Array<Record<string, unknown>>).map(
                  (link, i) => (
                    <div
                      key={i}
                      className="flex items-center justify-between py-2"
                    >
                      <div>
                        <p className="text-xs font-bold text-on-surface">
                          {(link.to_key as string) ?? (link.from_key as string)}
                        </p>
                        <p className="text-[9px] text-secondary uppercase tracking-widest">
                          {link.type as string}
                        </p>
                      </div>
                      <Link
                        to={`/graph/${(link.to_key as string) ?? ""}`}
                        className="material-symbols-outlined text-sm text-secondary hover:text-primary transition-colors"
                      >
                        arrow_forward
                      </Link>
                    </div>
                  )
                )}
              </div>
            ) : (
              <p className="text-xs text-secondary">No connections yet.</p>
            )}
          </div>
        </aside>
      </div>
    </div>
  );
}
