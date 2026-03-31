import { Link } from "react-router-dom";
import {
  useStats,
  useTopCompanies,
  useTrending,
  useAnomalies,
  useSync,
} from "@/hooks/useOntology";
import { SearchBar } from "@/components/SearchBar";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
} from "recharts";

function KpiCard({
  label,
  value,
  icon,
}: {
  label: string;
  value: string | number;
  icon: string;
}) {
  return (
    <div className="bg-surface-container/50 backdrop-blur-sm border border-outline p-6">
      <div className="flex items-center gap-2 text-[10px] text-secondary uppercase tracking-widest font-label mb-2">
        <span className="material-symbols-outlined text-primary text-sm">
          {icon}
        </span>
        {label}
      </div>
      <p className="text-3xl font-headline font-bold tracking-tighter text-on-surface">
        {value}
      </p>
    </div>
  );
}

function InsightCard({
  icon,
  title,
  children,
  color = "text-primary",
}: {
  icon: string;
  title: string;
  children: React.ReactNode;
  color?: string;
}) {
  return (
    <div className="bg-surface-container/50 backdrop-blur-sm border border-outline p-6">
      <div className="flex items-center gap-2 mb-4">
        <span className={`material-symbols-outlined text-sm ${color}`}>
          {icon}
        </span>
        <h3 className="text-[10px] uppercase tracking-[0.3em] font-bold text-primary font-label">
          {title}
        </h3>
      </div>
      {children}
    </div>
  );
}

export function Dashboard() {
  const { data: stats, isLoading } = useStats();
  const { data: topByMarketCap } = useTopCompanies("market_cap");
  const { data: trending } = useTrending();
  const { data: anomalies } = useAnomalies();
  const sync = useSync();

  const objectCounts = stats?.object_counts ?? {};
  const totalObjects = Object.values(objectCounts).reduce((a, b) => a + b, 0);

  const chartData = (topByMarketCap ?? []).map((c) => ({
    name: (c.name ?? c.key).slice(0, 12),
    value: Math.round((c.value ?? 0) / 1e9),
  }));

  return (
    <div>
      {/* Header */}
      <header className="mb-12 border-l-2 border-primary pl-8">
        <div className="flex items-center gap-2 text-primary font-label text-xs font-bold uppercase tracking-[0.2em] mb-4">
          <span className="w-2 h-2 bg-primary rounded-full animate-pulse" />
          System Node: Sovereign-01
        </div>
        <h2 className="text-5xl font-bold tracking-tighter text-on-surface mb-4 font-headline">
          Dashboard
        </h2>
        <p className="text-on-surface-variant max-w-2xl text-lg font-light leading-relaxed">
          Unified intelligence across 7 data sources. Monitor coverage,
          anomalies, and market dynamics.
        </p>
      </header>

      {/* Search */}
      <div className="mb-10 max-w-xl">
        <SearchBar />
      </div>

      {/* KPIs */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-10">
        <KpiCard
          label="Total Objects"
          value={isLoading ? "..." : totalObjects}
          icon="database"
        />
        <KpiCard
          label="Companies"
          value={isLoading ? "..." : objectCounts.company ?? 0}
          icon="domain"
        />
        <KpiCard
          label="Links"
          value={isLoading ? "..." : stats?.total_links ?? 0}
          icon="link"
        />
        <KpiCard
          label="Articles"
          value={isLoading ? "..." : objectCounts.article ?? 0}
          icon="article"
        />
      </div>

      {/* Main Grid */}
      <div className="grid grid-cols-12 gap-6">
        {/* Left: Chart + Trending */}
        <div className="col-span-12 lg:col-span-8 space-y-6">
          {/* Market Cap Chart */}
          <InsightCard icon="bar_chart" title="Top Companies by Market Cap ($B)">
            {chartData.length > 0 ? (
              <ResponsiveContainer width="100%" height={260}>
                <BarChart data={chartData}>
                  <XAxis
                    dataKey="name"
                    tick={{ fill: "#94a3b8", fontSize: 10 }}
                    axisLine={false}
                    tickLine={false}
                  />
                  <YAxis
                    tick={{ fill: "#94a3b8", fontSize: 10 }}
                    axisLine={false}
                    tickLine={false}
                  />
                  <Tooltip
                    contentStyle={{
                      background: "#0f172a",
                      border: "1px solid #334155",
                      borderRadius: "4px",
                      color: "#f8fafc",
                      fontSize: 12,
                    }}
                  />
                  <Bar dataKey="value" fill="#60a5fa" radius={[2, 2, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            ) : (
              <div className="py-8 text-center space-y-2">
                <p className="text-sm text-secondary">No market data yet.</p>
                <p className="text-xs text-secondary/60">
                  Set <code className="bg-surface-container-high px-1 py-0.5 text-primary text-[11px]">ALPHA_VANTAGE_KEY</code> in
                  .env, then sync.
                </p>
                <button
                  onClick={() => sync.mutate("yahoo_finance")}
                  disabled={sync.isPending}
                  className="mt-2 px-4 py-2 text-[10px] font-label font-bold uppercase tracking-widest border border-outline hover:border-primary/50 text-secondary hover:text-on-surface transition-all disabled:opacity-50"
                >
                  Sync Market Data
                </button>
              </div>
            )}
          </InsightCard>

          {/* Trending */}
          <InsightCard icon="trending_up" title="Trending — Most HN Mentions" color="text-orange-400">
            {trending && trending.length > 0 ? (
              <div className="space-y-2">
                {trending.slice(0, 6).map((t, i) => (
                  <Link
                    key={t.key}
                    to={`/company/${t.key}`}
                    className="flex items-center justify-between py-2 hover:bg-surface-container-high/30 px-2 -mx-2 transition-colors"
                  >
                    <div className="flex items-center gap-3">
                      <span className="text-[10px] text-secondary font-label font-bold w-5">
                        #{i + 1}
                      </span>
                      <span className="text-sm font-medium text-on-surface">
                        {t.name ?? t.key}
                      </span>
                    </div>
                    <div className="flex items-center gap-2">
                      {(() => {
                        const tp = (t as Record<string, unknown>).trend_pct;
                        if (tp === null || tp === undefined) {
                          return <span className="text-[10px] text-blue-400 font-label font-bold">new</span>;
                        }
                        const n = tp as number;
                        return (
                          <span className={`text-[10px] font-label font-bold ${
                            n > 0 ? "text-green-400" : n < 0 ? "text-red-400" : "text-secondary"
                          }`}>
                            {n > 0 ? "↑" : n < 0 ? "↓" : "→"} {Math.abs(n)}%
                          </span>
                        );
                      })()}
                      <span className="text-xs text-orange-400 font-label font-bold">
                        {t.mentions}
                      </span>
                    </div>
                  </Link>
                ))}
              </div>
            ) : (
              <p className="text-sm text-secondary">No trending data yet.</p>
            )}
          </InsightCard>
        </div>

        {/* Right sidebar */}
        <div className="col-span-12 lg:col-span-4 space-y-6">
          {/* Source Coverage */}
          <InsightCard icon="pie_chart" title="Source Coverage">
            {stats?.source_coverage ? (
              <div className="space-y-2">
                {Object.entries(stats.source_coverage)
                  .sort(([, a], [, b]) => (b as number) - (a as number))
                  .map(([source, count]) => (
                    <div key={source} className="flex items-center justify-between">
                      <span className="text-xs text-secondary capitalize">
                        {source.replace("_", " ")}
                      </span>
                      <span className="text-xs text-on-surface font-label font-bold">
                        {count as number} companies
                      </span>
                    </div>
                  ))}
              </div>
            ) : (
              <p className="text-sm text-secondary">Loading...</p>
            )}
          </InsightCard>

          {/* Anomalies */}
          <InsightCard icon="warning" title="Coverage Gaps" color="text-yellow-400">
            {anomalies && anomalies.length > 0 ? (
              <div className="space-y-2">
                {anomalies.slice(0, 5).map((a) => (
                  <div key={a.key} className="flex items-center justify-between py-1">
                    <span className="text-xs text-on-surface truncate max-w-[140px]">
                      {a.name ?? a.key}
                    </span>
                    <span className="text-[10px] text-yellow-400 font-label">
                      {Math.round(a.source_coverage * 100)}%
                    </span>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-xs text-secondary">No anomalies.</p>
            )}
          </InsightCard>

          {/* Sync Controls */}
          <InsightCard icon="sync" title="Data Sync">
            <div className="space-y-1.5">
              {["wikipedia", "github", "sec", "hn", "derived"].map((source) => (
                <button
                  key={source}
                  onClick={() => sync.mutate(source)}
                  disabled={sync.isPending}
                  className="w-full flex items-center justify-between px-3 py-2 bg-surface-container-high border border-outline hover:border-primary/50 text-[10px] font-label font-bold uppercase tracking-widest text-secondary hover:text-on-surface transition-all disabled:opacity-50"
                >
                  {source}
                  <span className="material-symbols-outlined text-sm">sync</span>
                </button>
              ))}
            </div>
          </InsightCard>
        </div>
      </div>
    </div>
  );
}
