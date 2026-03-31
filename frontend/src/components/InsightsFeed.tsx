import { useAnomalies } from "@/hooks/useOntology";

export function InsightsFeed() {
  const { data: anomalies, isLoading } = useAnomalies();

  if (isLoading) {
    return (
      <div className="animate-pulse space-y-3">
        {[1, 2, 3].map((i) => (
          <div key={i} className="h-12 bg-surface-container-high" />
        ))}
      </div>
    );
  }

  if (!anomalies?.length) {
    return (
      <p className="text-xs text-secondary">No anomalies detected.</p>
    );
  }

  return (
    <div className="space-y-3">
      {anomalies.slice(0, 8).map((a) => (
        <div
          key={a.key}
          className="flex items-center justify-between py-3 group"
        >
          <div className="flex items-start gap-3">
            <span className="material-symbols-outlined text-yellow-400 mt-0.5 text-sm">
              warning
            </span>
            <div>
              <p className="text-xs font-bold text-on-surface tracking-tight">
                {a.name ?? a.key}
              </p>
              <p className="text-[10px] text-secondary mt-0.5">
                Missing: {a.missing_sources.join(", ")}
              </p>
            </div>
          </div>
          <div className="text-[10px] font-label font-bold text-secondary">
            {Math.round(a.source_coverage * 100)}%
          </div>
        </div>
      ))}
    </div>
  );
}
