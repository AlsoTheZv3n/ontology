import { useEffect, useState } from "react";
import { Link } from "react-router-dom";

interface Alert {
  id: string;
  title: string;
  description: string;
  severity: "high" | "medium" | "low";
  source: string;
  company_key?: string;
  metric?: string;
  value?: number;
  z_score?: number;
}

const SEVERITY_STYLES: Record<
  string,
  { bar: string; badge: string; badgeText: string }
> = {
  high: {
    bar: "bg-red-500",
    badge: "bg-red-500/20 text-red-400 border-red-500/30",
    badgeText: "HIGH",
  },
  medium: {
    bar: "bg-yellow-500",
    badge: "bg-yellow-500/20 text-yellow-400 border-yellow-500/30",
    badgeText: "MED",
  },
  low: {
    bar: "bg-blue-500",
    badge: "bg-blue-500/20 text-blue-400 border-blue-500/30",
    badgeText: "LOW",
  },
};

export function Alerts() {
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch("/api/insights/alerts")
      .then((r) => r.json())
      .then((d) => {
        setAlerts(d);
        setLoading(false);
      })
      .catch(() => setLoading(false));
  }, []);

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
          Statistical anomaly detection across all company metrics. Z-score based
          outlier identification using scikit-learn.
        </p>
      </header>

      {/* Stats */}
      {!loading && (
        <div className="flex gap-4 mb-8">
          {["high", "medium", "low"].map((sev) => {
            const count = alerts.filter((a) => a.severity === sev).length;
            const s = SEVERITY_STYLES[sev];
            return (
              <div
                key={sev}
                className={`px-4 py-2 border ${s.badge} text-xs font-label font-bold uppercase tracking-widest`}
              >
                {s.badgeText}: {count}
              </div>
            );
          })}
          <div className="px-4 py-2 border border-outline text-xs font-label text-secondary uppercase tracking-widest">
            Total: {alerts.length}
          </div>
        </div>
      )}

      {/* Loading */}
      {loading && (
        <div className="animate-pulse space-y-3">
          {[1, 2, 3].map((i) => (
            <div key={i} className="h-24 bg-surface-container-high" />
          ))}
        </div>
      )}

      {/* Empty */}
      {!loading && alerts.length === 0 && (
        <div className="py-16 text-center border border-outline bg-surface-container/30">
          <span className="material-symbols-outlined text-4xl text-secondary/30 mb-4">
            check_circle
          </span>
          <p className="text-sm text-secondary">
            No anomalies detected. All metrics within normal range.
          </p>
        </div>
      )}

      {/* Alert Cards */}
      <div className="space-y-3">
        {alerts.map((alert) => {
          const sev = SEVERITY_STYLES[alert.severity] ?? SEVERITY_STYLES.low;
          return (
            <div
              key={alert.id}
              className="flex bg-surface-container/50 border border-outline hover:border-primary/30 transition-colors overflow-hidden"
            >
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
                  {alert.z_score && (
                    <span className="text-xs font-label font-bold text-on-surface bg-surface-container-high px-2 py-0.5 border border-outline">
                      {alert.z_score}σ
                    </span>
                  )}
                </div>

                <p className="text-xs text-on-surface-variant leading-relaxed mb-3">
                  {alert.description}
                </p>

                <div className="flex items-center gap-2">
                  <span className="text-[9px] font-label font-bold uppercase tracking-widest text-secondary bg-surface-container-high px-1.5 py-0.5 border border-outline">
                    {alert.source}
                  </span>
                  {alert.company_key && (
                    <Link
                      to={`/company/${alert.company_key}`}
                      className="text-[9px] font-label font-bold uppercase tracking-widest text-primary hover:text-primary/70 transition-colors"
                    >
                      View Company →
                    </Link>
                  )}
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
