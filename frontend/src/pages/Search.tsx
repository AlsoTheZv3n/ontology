import { useState, useMemo } from "react";
import { useSearchParams, Link } from "react-router-dom";
import { useSearch } from "@/hooks/useOntology";
import { SourceBadge } from "@/components/SourceBadge";

interface SearchResult {
  key: string;
  type: string;
  properties: Record<string, unknown>;
  sources?: Record<string, unknown>;
}

const TYPE_ORDER = ["company", "person", "article", "repository", "event"];

function CompanyCard({ obj }: { obj: SearchResult }) {
  const p = obj.properties;
  return (
    <Link
      to={`/company/${obj.key}`}
      className="block bg-surface-container border border-outline hover:border-primary/40 p-5 transition-all group"
    >
      <div className="flex items-start justify-between mb-2">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="text-[9px] font-bold text-indigo-400 uppercase tracking-widest">Company</span>
            {p.ticker && <span className="text-[9px] font-mono text-secondary bg-surface px-2 py-0.5">{String(p.ticker)}</span>}
            {p.sector && <span className="text-[9px] text-secondary">{String(p.sector)}</span>}
          </div>
          <h3 className="text-base font-headline font-bold text-on-surface group-hover:text-primary transition-colors">
            {(p.name as string) ?? obj.key}
          </h3>
          {p.description && (
            <p className="text-xs text-secondary mt-1 line-clamp-2 max-w-2xl">{String(p.description).slice(0, 180)}</p>
          )}
        </div>
        {p.market_cap && (
          <div className="text-right flex-shrink-0 ml-6">
            <span className="text-[9px] text-secondary uppercase tracking-widest">Mkt Cap</span>
            <p className="text-sm font-bold text-on-surface">
              {Number(p.market_cap) > 1e12 ? `$${(Number(p.market_cap) / 1e12).toFixed(2)}T` : `$${(Number(p.market_cap) / 1e9).toFixed(0)}B`}
            </p>
          </div>
        )}
      </div>
      <div className="flex items-center gap-4 flex-wrap text-[10px] text-secondary">
        {p.ceo && <span>CEO: <span className="text-on-surface">{String(p.ceo)}</span></span>}
        {p.founded && <span>Founded: <span className="text-on-surface">{String(Math.round(Number(p.founded)))}</span></span>}
        {p.employees && <span>Employees: <span className="text-on-surface">{Number(p.employees).toLocaleString()}</span></span>}
      </div>
      {obj.sources && Object.keys(obj.sources).length > 0 && (
        <div className="flex gap-1 mt-3 flex-wrap">
          {Object.keys(obj.sources).map((s) => <SourceBadge key={s} source={s} />)}
        </div>
      )}
    </Link>
  );
}

function PersonCard({ obj }: { obj: SearchResult }) {
  const p = obj.properties;
  return (
    <Link
      to={`/graph/${obj.key}`}
      className="block bg-surface-container border border-outline hover:border-sky-400/40 p-4 transition-all group"
    >
      <div className="flex items-center gap-3">
        <div className="w-10 h-10 rounded-full bg-sky-900/40 border border-sky-400/30 flex items-center justify-center text-sky-400 font-bold text-sm flex-shrink-0">
          {String(p.name ?? obj.key).charAt(0).toUpperCase()}
        </div>
        <div>
          <div className="flex items-center gap-2">
            <span className="text-[9px] font-bold text-sky-400 uppercase tracking-widest">Person</span>
            {p.role && <span className="text-[9px] text-secondary">{String(p.role)}</span>}
          </div>
          <h3 className="text-sm font-bold text-on-surface group-hover:text-sky-400 transition-colors">
            {String(p.name ?? obj.key)}
          </h3>
          {p.company_key && <p className="text-xs text-secondary">at <span className="text-on-surface">{String(p.company_key)}</span></p>}
        </div>
      </div>
    </Link>
  );
}

function ArticleCard({ obj }: { obj: SearchResult }) {
  const p = obj.properties;
  return (
    <div className="bg-surface-container border border-outline hover:border-orange-400/40 p-4 transition-all">
      <div className="flex items-center gap-2 mb-1">
        <span className="text-[9px] font-bold text-orange-400 uppercase tracking-widest">Article</span>
        {p.source && <span className="text-[9px] text-secondary capitalize">{String(p.source)}</span>}
      </div>
      <h3 className="text-sm font-medium text-on-surface line-clamp-2">{String(p.title ?? obj.key)}</h3>
    </div>
  );
}

function RepoCard({ obj }: { obj: SearchResult }) {
  const p = obj.properties;
  return (
    <div className="bg-surface-container border border-outline hover:border-emerald-400/40 p-4 transition-all">
      <div className="flex items-start justify-between gap-4">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="text-[9px] font-bold text-emerald-400 uppercase tracking-widest">Repository</span>
            {p.language && <span className="text-[9px] font-mono text-secondary bg-surface px-2 py-0.5">{String(p.language)}</span>}
          </div>
          <h3 className="text-sm font-mono font-medium text-on-surface">{obj.key}</h3>
          {p.description && <p className="text-xs text-secondary mt-1 line-clamp-1">{String(p.description)}</p>}
        </div>
        <div className="flex-shrink-0 text-right">
          {p.stars && <p className="text-xs text-yellow-400 font-bold">&#9733; {Number(p.stars).toLocaleString()}</p>}
          {p.forks && <p className="text-[9px] text-secondary">{Number(p.forks).toLocaleString()} forks</p>}
        </div>
      </div>
    </div>
  );
}

function GenericCard({ obj }: { obj: SearchResult }) {
  const p = obj.properties;
  return (
    <div className="bg-surface-container border border-outline p-4">
      <span className="text-[9px] text-secondary uppercase tracking-widest">{obj.type}</span>
      <p className="text-sm text-on-surface mt-1">{(p.name as string) ?? (p.title as string) ?? obj.key}</p>
    </div>
  );
}

export function Search() {
  const [searchParams, setSearchParams] = useSearchParams();
  const query = searchParams.get("q") ?? "";
  const [activeType, setActiveType] = useState("all");

  const { data: results, isLoading } = useSearch(query);

  const grouped = useMemo(() => {
    if (!results) return {};
    return (results as SearchResult[]).reduce((acc, r) => {
      acc[r.type] = (acc[r.type] ?? 0) + 1;
      return acc;
    }, {} as Record<string, number>);
  }, [results]);

  const filtered = useMemo(() => {
    if (!results) return [];
    if (activeType === "all") return results as SearchResult[];
    return (results as SearchResult[]).filter((r) => r.type === activeType);
  }, [results, activeType]);

  return (
    <div>
      <div className="mb-8">
        <div className="relative">
          <span className="absolute left-4 top-1/2 -translate-y-1/2 material-symbols-outlined text-secondary text-lg">search</span>
          <input
            type="text"
            value={query}
            onChange={(e) => setSearchParams({ q: e.target.value }, { replace: true })}
            placeholder="Search companies, people, articles, repositories..."
            autoFocus
            className="w-full pl-12 pr-4 py-4 bg-surface-container border border-outline text-on-surface placeholder:text-secondary text-sm focus:outline-none focus:border-primary/50 font-label tracking-wide"
          />
          {isLoading && (
            <span className="absolute right-4 top-1/2 -translate-y-1/2 material-symbols-outlined text-secondary text-sm animate-spin">autorenew</span>
          )}
        </div>
      </div>

      {query && results && (
        <>
          <div className="flex gap-2 mb-6 flex-wrap">
            <button
              onClick={() => setActiveType("all")}
              className={`px-4 py-1.5 text-[10px] font-label font-bold uppercase tracking-widest border transition-all ${activeType === "all" ? "border-primary text-primary bg-primary/10" : "border-outline text-secondary hover:text-on-surface"}`}
            >
              All ({(results as unknown[]).length})
            </button>
            {TYPE_ORDER.filter((t) => grouped[t]).map((type) => (
              <button
                key={type}
                onClick={() => setActiveType(type)}
                className={`px-4 py-1.5 text-[10px] font-label font-bold uppercase tracking-widest border transition-all ${activeType === type ? "border-primary text-primary bg-primary/10" : "border-outline text-secondary hover:text-on-surface"}`}
              >
                {type} ({grouped[type]})
              </button>
            ))}
          </div>

          <div className="space-y-2">
            {filtered.map((obj) => {
              switch (obj.type) {
                case "company": return <CompanyCard key={obj.key} obj={obj} />;
                case "person": return <PersonCard key={obj.key} obj={obj} />;
                case "article": return <ArticleCard key={obj.key} obj={obj} />;
                case "repository": return <RepoCard key={obj.key} obj={obj} />;
                default: return <GenericCard key={obj.key} obj={obj} />;
              }
            })}
          </div>

          {filtered.length === 0 && (
            <p className="text-secondary text-sm text-center py-12">No results for &ldquo;{query}&rdquo;</p>
          )}
        </>
      )}

      {!query && (
        <div className="text-center py-20">
          <p className="text-secondary text-sm">Search across companies, persons, articles and repositories</p>
          <div className="flex gap-3 justify-center mt-4 flex-wrap">
            {["nvidia", "anthropic", "jensen huang", "react", "apple"].map((q) => (
              <button
                key={q}
                onClick={() => setSearchParams({ q })}
                className="text-[10px] font-label uppercase tracking-widest px-3 py-1.5 border border-outline text-secondary hover:text-on-surface hover:border-primary/30 transition-all"
              >
                {q}
              </button>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
