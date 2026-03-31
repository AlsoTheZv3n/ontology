const SOURCE_COLORS: Record<string, string> = {
  wikipedia: "bg-blue-500/10 text-blue-400 border-blue-500/30",
  github: "bg-purple-500/10 text-purple-400 border-purple-500/30",
  yahoo_finance: "bg-yellow-500/10 text-yellow-400 border-yellow-500/30",
  sec_edgar: "bg-green-500/10 text-green-400 border-green-500/30",
  hn_rss: "bg-orange-500/10 text-orange-400 border-orange-500/30",
  forbes: "bg-red-500/10 text-red-400 border-red-500/30",
  patents: "bg-cyan-500/10 text-cyan-400 border-cyan-500/30",
};

interface SourceBadgeProps {
  source: string;
}

export function SourceBadge({ source }: SourceBadgeProps) {
  const color = SOURCE_COLORS[source] ?? "bg-slate-500/10 text-slate-400 border-slate-500/30";
  return (
    <span
      className={`inline-block px-2 py-0.5 text-[9px] font-bold uppercase tracking-widest border ${color}`}
    >
      {source.replace("_", " ")}
    </span>
  );
}
