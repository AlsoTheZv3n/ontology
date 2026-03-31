import { useEffect, useState } from "react";

interface FeedItem {
  label: string;
  event_type: string;
  date: string;
  time_ago: string;
  key?: string;
  source?: string;
}

const DOT_COLORS: Record<string, string> = {
  sec_filing: "bg-blue-400",
  hackernews: "bg-green-400",
  patent: "bg-purple-400",
  positive: "bg-green-400",
  negative: "bg-red-400",
  info: "bg-blue-400",
  warning: "bg-yellow-400",
};

function dotColor(eventType: string): string {
  return DOT_COLORS[eventType] ?? "bg-slate-400";
}

function dotRing(eventType: string): string {
  const map: Record<string, string> = {
    sec_filing: "ring-blue-400/30",
    hackernews: "ring-green-400/30",
    patent: "ring-purple-400/30",
    positive: "ring-green-400/30",
    negative: "ring-red-400/30",
    info: "ring-blue-400/30",
    warning: "ring-yellow-400/30",
  };
  return map[eventType] ?? "ring-slate-400/30";
}

export function Feed() {
  const [items, setItems] = useState<FeedItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetch("/api/insights/feed?limit=50")
      .then((r) => {
        if (!r.ok) throw new Error(`${r.status} ${r.statusText}`);
        return r.json();
      })
      .then((data) => {
        setItems(Array.isArray(data) ? data : data.items ?? []);
        setLoading(false);
      })
      .catch((err) => {
        setError(err.message);
        setLoading(false);
      });
  }, []);

  return (
    <div>
      {/* Header */}
      <header className="mb-12 border-l-2 border-primary pl-8">
        <div className="flex items-center gap-2 text-primary font-label text-xs font-bold uppercase tracking-[0.2em] mb-4">
          <span className="w-2 h-2 bg-primary rounded-full animate-pulse" />
          Live Stream
        </div>
        <h2 className="text-5xl font-bold tracking-tighter text-on-surface mb-4 font-headline">
          Intelligence Feed
        </h2>
        <p className="text-on-surface-variant max-w-2xl text-lg font-light leading-relaxed">
          Chronological stream of events across all monitored sources.
        </p>
      </header>

      {/* Feed */}
      {loading && (
        <p className="text-sm text-secondary font-label">Loading feed...</p>
      )}
      {error && (
        <p className="text-sm text-red-400 font-label">Error: {error}</p>
      )}

      {!loading && !error && items.length === 0 && (
        <div className="bg-surface-container/50 border border-outline p-8 text-center">
          <p className="text-sm text-secondary">No feed items yet. Sync some data sources first.</p>
        </div>
      )}

      {!loading && !error && items.length > 0 && (
        <div className="space-y-1">
          {items.map((item, i) => (
            <div
              key={`${item.key ?? item.label}-${i}`}
              className="flex items-center gap-4 px-4 py-3 bg-surface-container/50 border border-outline hover:border-primary/30 transition-colors"
            >
              {/* Colored dot */}
              <span
                className={`w-2.5 h-2.5 rounded-full ring-4 ${dotColor(item.event_type)} ${dotRing(item.event_type)} shrink-0`}
              />

              {/* Label */}
              <span className="text-sm text-on-surface font-medium flex-1 truncate">
                {item.label}
              </span>

              {/* Event type badge */}
              <span className="text-[10px] font-label font-bold uppercase tracking-widest text-secondary bg-surface-container-high px-2 py-0.5 shrink-0">
                {item.event_type.replace("_", " ")}
              </span>

              {/* Date */}
              <span className="text-xs text-secondary font-label shrink-0 w-24 text-right">
                {item.date}
              </span>

              {/* Time ago */}
              <span className="text-xs text-on-surface-variant shrink-0 w-20 text-right">
                {item.time_ago}
              </span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
