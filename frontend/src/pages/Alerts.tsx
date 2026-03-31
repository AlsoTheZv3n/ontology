interface MockAlert {
  id: string;
  title: string;
  description: string;
  severity: "high" | "medium" | "low";
  source: string;
  timestamp: string;
}

const SEVERITY_STYLES: Record<string, { bar: string; badge: string; badgeText: string }> = {
  high:   { bar: "bg-red-500",    badge: "bg-red-500/20 text-red-400 border-red-500/30",       badgeText: "HIGH" },
  medium: { bar: "bg-yellow-500", badge: "bg-yellow-500/20 text-yellow-400 border-yellow-500/30", badgeText: "MED" },
  low:    { bar: "bg-blue-500",   badge: "bg-blue-500/20 text-blue-400 border-blue-500/30",     badgeText: "LOW" },
};

const MOCK_ALERTS: MockAlert[] = [
  {
    id: "alert-1",
    title: "NVIDIA Sentiment Anomaly",
    description:
      "FinBERT detected a 2.4 std deviation shift in sentiment across 147 SEC filings and earnings transcripts. Bearish signal diverges from price action.",
    severity: "high",
    source: "SEC Filings + HackerNews",
    timestamp: "2026-03-31T08:12:00Z",
  },
  {
    id: "alert-2",
    title: "Lithium Price Spike +4.2%",
    description:
      "Macro indicator for lithium carbonate exceeded 3-month rolling average by 4.2%. Correlated entities: Albemarle, SQM, Ganfeng Lithium.",
    severity: "high",
    source: "World Bank Indicators",
    timestamp: "2026-03-31T06:45:00Z",
  },
  {
    id: "alert-3",
    title: "Anthropic GitHub Activity +340%",
    description:
      "Repository commit frequency for Anthropic-affiliated repos surged 340% week-over-week. 12 new repositories detected.",
    severity: "medium",
    source: "GitHub",
    timestamp: "2026-03-30T22:30:00Z",
  },
  {
    id: "alert-4",
    title: "Apple Patent Cluster Detected",
    description:
      "17 new USPTO patent filings in spatial computing category within 48h. Unusual clustering suggests imminent product announcement.",
    severity: "medium",
    source: "USPTO Patents",
    timestamp: "2026-03-30T14:00:00Z",
  },
  {
    id: "alert-5",
    title: "EU Carbon Credit Volatility",
    description:
      "ETS carbon credit pricing entered high-volatility regime. Z-score: 1.8. Below alert threshold but trending upward.",
    severity: "low",
    source: "World Bank + Derived",
    timestamp: "2026-03-29T19:15:00Z",
  },
];

export function Alerts() {
  return (
    <div>
      {/* Header */}
      <header className="mb-12 border-l-2 border-primary pl-8">
        <div className="flex items-center gap-2 text-primary font-label text-xs font-bold uppercase tracking-[0.2em] mb-4">
          <span className="w-2 h-2 bg-primary rounded-full animate-pulse" />
          Anomaly Detection
        </div>
        <h2 className="text-5xl font-bold tracking-tighter text-on-surface mb-4 font-headline">
          Alerts
        </h2>
        <p className="text-on-surface-variant max-w-2xl text-lg font-light leading-relaxed">
          ML-powered anomaly detection — coming soon with FinBERT and scikit-learn.
          Showing sample alerts to preview the interface.
        </p>
      </header>

      {/* Coming Soon Banner */}
      <div className="mb-8 px-5 py-4 bg-blue-500/10 border border-blue-500/30 flex items-center gap-3">
        <span className="material-symbols-outlined text-blue-400 text-sm">science</span>
        <p className="text-sm text-blue-300">
          <span className="font-label font-bold uppercase tracking-widest text-[10px] text-blue-400 mr-2">
            Preview Mode
          </span>
          These alerts are mock data. The ML pipeline (FinBERT sentiment, scikit-learn anomaly detection)
          will replace this with live signals.
        </p>
      </div>

      {/* Alert Cards */}
      <div className="space-y-3">
        {MOCK_ALERTS.map((alert) => {
          const sev = SEVERITY_STYLES[alert.severity];
          return (
            <div
              key={alert.id}
              className="flex bg-surface-container/50 border border-outline hover:border-primary/30 transition-colors overflow-hidden"
            >
              {/* Severity bar */}
              <div className={`w-1.5 shrink-0 ${sev.bar}`} />

              <div className="flex-1 p-5">
                <div className="flex items-start justify-between gap-4 mb-2">
                  <div className="flex items-center gap-3">
                    <span
                      className={`px-2 py-0.5 text-[9px] font-label font-bold uppercase tracking-widest border ${sev.badge}`}
                    >
                      {sev.badgeText}
                    </span>
                    <h4 className="text-sm font-medium text-on-surface">
                      {alert.title}
                    </h4>
                  </div>
                  <span className="text-[10px] text-secondary font-label shrink-0">
                    {new Date(alert.timestamp).toLocaleDateString("en-US", {
                      month: "short",
                      day: "numeric",
                      hour: "2-digit",
                      minute: "2-digit",
                    })}
                  </span>
                </div>

                <p className="text-xs text-on-surface-variant leading-relaxed mb-3">
                  {alert.description}
                </p>

                <div className="flex items-center gap-2">
                  <span className="text-[9px] font-label font-bold uppercase tracking-widest text-secondary bg-surface-container-high px-1.5 py-0.5 border border-outline">
                    {alert.source}
                  </span>
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
