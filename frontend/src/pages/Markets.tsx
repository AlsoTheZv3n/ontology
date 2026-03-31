import { useEffect, useState } from "react";

interface MacroIndicator {
  name: string;
  value: number | string;
  year: number | string;
  country: string;
}

interface TopCompany {
  name: string;
  key: string;
  market_cap: number;
  revenue: number | string;
  sector: string;
}

interface MarketsData {
  macro_indicators: MacroIndicator[];
  top_companies: TopCompany[];
}

function formatMarketCap(val: number): string {
  if (val >= 1e12) return `$${(val / 1e12).toFixed(2)}T`;
  if (val >= 1e9) return `$${(val / 1e9).toFixed(1)}B`;
  if (val >= 1e6) return `$${(val / 1e6).toFixed(0)}M`;
  return `$${val.toLocaleString()}`;
}

export function Markets() {
  const [data, setData] = useState<MarketsData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetch("/api/insights/markets")
      .then((r) => {
        if (!r.ok) throw new Error(`${r.status} ${r.statusText}`);
        return r.json();
      })
      .then((d) => {
        setData(d);
        setLoading(false);
      })
      .catch((err) => {
        setError(err.message);
        setLoading(false);
      });
  }, []);

  // Group macro indicators by country
  const grouped: Record<string, MacroIndicator[]> = {};
  (data?.macro_indicators ?? []).forEach((ind) => {
    const country = ind.country || "Global";
    if (!grouped[country]) grouped[country] = [];
    grouped[country].push(ind);
  });

  return (
    <div>
      {/* Header */}
      <header className="mb-12 border-l-2 border-primary pl-8">
        <div className="flex items-center gap-2 text-primary font-label text-xs font-bold uppercase tracking-[0.2em] mb-4">
          <span className="w-2 h-2 bg-primary rounded-full animate-pulse" />
          Market Intelligence
        </div>
        <h2 className="text-5xl font-bold tracking-tighter text-on-surface mb-4 font-headline">
          Markets
        </h2>
        <p className="text-on-surface-variant max-w-2xl text-lg font-light leading-relaxed">
          Macro indicators and top companies by market capitalization.
        </p>
      </header>

      {loading && (
        <p className="text-sm text-secondary font-label">Loading markets...</p>
      )}
      {error && (
        <p className="text-sm text-red-400 font-label">Error: {error}</p>
      )}

      {!loading && !error && (
        <div className="grid grid-cols-12 gap-6">
          {/* Left: Macro Indicators */}
          <div className="col-span-12 lg:col-span-5 space-y-6">
            <div className="flex items-center gap-2 mb-2">
              <span className="material-symbols-outlined text-sm text-primary">public</span>
              <h3 className="text-[10px] uppercase tracking-[0.3em] font-bold text-primary font-label">
                Macro Indicators
              </h3>
            </div>

            {Object.keys(grouped).length === 0 && (
              <div className="bg-surface-container/50 border border-outline p-6 text-center">
                <p className="text-sm text-secondary">No macro data available.</p>
              </div>
            )}

            {Object.entries(grouped).map(([country, indicators]) => (
              <div
                key={country}
                className="bg-surface-container/50 border border-outline p-5"
              >
                <h4 className="text-xs font-label font-bold uppercase tracking-widest text-amber-400 mb-3">
                  {country}
                </h4>
                <div className="space-y-2">
                  {indicators.map((ind, i) => (
                    <div
                      key={`${ind.name}-${i}`}
                      className="flex items-center justify-between py-1"
                    >
                      <span className="text-sm text-on-surface">{ind.name}</span>
                      <div className="flex items-center gap-3">
                        <span className="text-sm font-headline font-bold text-on-surface">
                          {typeof ind.value === "number"
                            ? ind.value.toLocaleString()
                            : ind.value}
                        </span>
                        <span className="text-[10px] text-secondary font-label">
                          {ind.year}
                        </span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            ))}
          </div>

          {/* Right: Top Companies */}
          <div className="col-span-12 lg:col-span-7">
            <div className="flex items-center gap-2 mb-4">
              <span className="material-symbols-outlined text-sm text-primary">domain</span>
              <h3 className="text-[10px] uppercase tracking-[0.3em] font-bold text-primary font-label">
                Top Companies
              </h3>
            </div>

            {(data?.top_companies ?? []).length === 0 ? (
              <div className="bg-surface-container/50 border border-outline p-6 text-center">
                <p className="text-sm text-secondary">No company data available.</p>
              </div>
            ) : (
              <div className="bg-surface-container/50 border border-outline overflow-hidden">
                <table className="w-full">
                  <thead>
                    <tr className="border-b border-outline">
                      <th className="text-left text-[10px] font-label font-bold uppercase tracking-widest text-secondary px-4 py-3">
                        Name
                      </th>
                      <th className="text-right text-[10px] font-label font-bold uppercase tracking-widest text-secondary px-4 py-3">
                        Market Cap
                      </th>
                      <th className="text-right text-[10px] font-label font-bold uppercase tracking-widest text-secondary px-4 py-3">
                        Revenue
                      </th>
                      <th className="text-left text-[10px] font-label font-bold uppercase tracking-widest text-secondary px-4 py-3">
                        Sector
                      </th>
                    </tr>
                  </thead>
                  <tbody>
                    {(data?.top_companies ?? []).map((c) => (
                      <tr
                        key={c.key}
                        className="border-b border-outline/50 hover:bg-surface-container-high/30 transition-colors"
                      >
                        <td className="px-4 py-3 text-sm text-on-surface font-medium">
                          {c.name}
                        </td>
                        <td className="px-4 py-3 text-sm text-on-surface font-headline font-bold text-right">
                          {formatMarketCap(c.market_cap)}
                        </td>
                        <td className="px-4 py-3 text-sm text-secondary text-right">
                          {typeof c.revenue === "number"
                            ? formatMarketCap(c.revenue)
                            : c.revenue || "—"}
                        </td>
                        <td className="px-4 py-3 text-xs text-secondary font-label">
                          {c.sector || "—"}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
