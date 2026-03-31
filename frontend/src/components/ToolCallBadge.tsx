import type { ToolCall } from "@/hooks/useChat";

const TOOL_LABELS: Record<string, string> = {
  search_objects: "Searching ontology",
  get_object: "Fetching object",
  get_links: "Traversing graph",
  compare_objects: "Comparing objects",
  get_anomalies: "Scanning anomalies",
  get_timeline: "Loading timeline",
  rank_objects: "Ranking by metric",
  get_market_data: "Fetching market data",
  search_news: "Searching news",
  search_research: "Searching research",
  get_package_stats: "Package stats",
};

const TOOL_COLORS: Record<string, string> = {
  search_objects: "bg-blue-500/10 text-blue-400 border-blue-500/30",
  get_object: "bg-purple-500/10 text-purple-400 border-purple-500/30",
  get_links: "bg-cyan-500/10 text-cyan-400 border-cyan-500/30",
  compare_objects: "bg-yellow-500/10 text-yellow-400 border-yellow-500/30",
  get_anomalies: "bg-red-500/10 text-red-400 border-red-500/30",
  get_timeline: "bg-green-500/10 text-green-400 border-green-500/30",
  rank_objects: "bg-primary/10 text-primary border-primary/30",
  get_market_data: "bg-emerald-500/10 text-emerald-400 border-emerald-500/30",
  search_news: "bg-orange-500/10 text-orange-400 border-orange-500/30",
  search_research: "bg-violet-500/10 text-violet-400 border-violet-500/30",
  get_package_stats: "bg-pink-500/10 text-pink-400 border-pink-500/30",
};

interface Props {
  toolCall: ToolCall;
}

export function ToolCallBadge({ toolCall }: Props) {
  const label = TOOL_LABELS[toolCall.name] ?? toolCall.name;
  const colors =
    TOOL_COLORS[toolCall.name] ?? "bg-slate-500/10 text-slate-400 border-slate-500/30";

  const inputLabel = Object.entries(toolCall.input)
    .filter(([k]) => ["query", "key", "keys", "metric"].includes(k))
    .map(([, v]) => (Array.isArray(v) ? v.join(", ") : String(v)))
    .join(" · ");

  return (
    <div
      className={`flex items-center gap-2 px-3 py-1.5 border text-[10px] font-label font-bold uppercase tracking-widest w-fit ${colors}`}
    >
      {toolCall.status === "pending" ? (
        <span className="flex gap-0.5">
          <span className="w-1 h-1 rounded-full bg-current animate-bounce [animation-delay:0ms]" />
          <span className="w-1 h-1 rounded-full bg-current animate-bounce [animation-delay:150ms]" />
          <span className="w-1 h-1 rounded-full bg-current animate-bounce [animation-delay:300ms]" />
        </span>
      ) : (
        <span className="material-symbols-outlined text-xs">check</span>
      )}

      <span>{label}</span>

      {inputLabel && (
        <span className="opacity-60 font-normal normal-case tracking-normal">
          {inputLabel.length > 30 ? inputLabel.slice(0, 30) + "…" : inputLabel}
        </span>
      )}

      {toolCall.status === "done" && toolCall.result && (
        <span className="opacity-50 normal-case tracking-normal">
          {toolCall.result.count !== undefined
            ? `${toolCall.result.count} results`
            : toolCall.result.error
              ? "error"
              : "ok"}
        </span>
      )}
    </div>
  );
}
