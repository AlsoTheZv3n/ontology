import { useState, useEffect, useRef, useMemo } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { useGraph, useObjects } from "@/hooks/useOntology";
import { GraphView } from "@/components/GraphView";
import { GraphFilterPanel, defaultFilters } from "@/components/GraphFilterPanel";
import { NodeDetailPanel } from "@/components/NodeDetailPanel";
import { api } from "@/lib/api";

export function Graph() {
  const { rootKey } = useParams();
  const navigate = useNavigate();
  const [input, setInput] = useState(rootKey ?? "");
  const [activeRoot, setActiveRoot] = useState(rootKey ?? "");
  const [depth, setDepth] = useState(2);

  const [filters, setFilters] = useState(defaultFilters);
  const [selectedNode, setSelectedNode] = useState<{ key: string; type: string } | null>(null);
  const { data, isLoading, error } = useGraph(activeRoot, depth);
  const { data: companies } = useObjects({ type: "company" });

  // Compute stats for filter panel
  const graphStats = useMemo(() => {
    if (!data) return undefined;
    const byType: Record<string, number> = {};
    data.nodes.forEach((n) => { byType[n.type] = (byType[n.type] ?? 0) + 1; });
    return { nodes: data.nodes.length, edges: data.edges.length, byType };
  }, [data]);

  // Autocomplete state
  const [suggestions, setSuggestions] = useState<{ key: string; type: string; name: string }[]>([]);
  const [showSuggestions, setShowSuggestions] = useState(false);
  const [activeIdx, setActiveIdx] = useState(-1);
  const wrapperRef = useRef<HTMLDivElement>(null);
  const debounceRef = useRef<ReturnType<typeof setTimeout>>();

  useEffect(() => {
    if (input.trim().length < 1) {
      setSuggestions([]);
      setShowSuggestions(false);
      return;
    }
    clearTimeout(debounceRef.current);
    debounceRef.current = setTimeout(async () => {
      try {
        const results = await api.suggest(input.trim());
        setSuggestions(results);
        setShowSuggestions(results.length > 0);
        setActiveIdx(-1);
      } catch { setSuggestions([]); }
    }, 150);
    return () => clearTimeout(debounceRef.current);
  }, [input]);

  useEffect(() => {
    const handler = (e: MouseEvent) => {
      if (wrapperRef.current && !wrapperRef.current.contains(e.target as Node))
        setShowSuggestions(false);
    };
    document.addEventListener("mousedown", handler);
    return () => document.removeEventListener("mousedown", handler);
  }, []);

  const selectCompany = (key: string) => {
    setInput(key);
    setActiveRoot(key);
    navigate(`/graph/${key}`);
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (activeIdx >= 0 && suggestions[activeIdx]) {
      selectCompany(suggestions[activeIdx].key);
      setShowSuggestions(false);
    } else if (input.trim()) {
      selectCompany(input.trim().toLowerCase());
      setShowSuggestions(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (!showSuggestions) return;
    if (e.key === "ArrowDown") { e.preventDefault(); setActiveIdx((i) => Math.min(i + 1, suggestions.length - 1)); }
    else if (e.key === "ArrowUp") { e.preventDefault(); setActiveIdx((i) => Math.max(i - 1, -1)); }
    else if (e.key === "Escape") setShowSuggestions(false);
  };

  return (
    <div>
      <header className="mb-12 border-l-2 border-primary pl-8">
        <h2 className="text-5xl font-bold tracking-tighter text-on-surface mb-4 font-headline">
          Graph Explorer
        </h2>
        <p className="text-on-surface-variant max-w-2xl text-lg font-light leading-relaxed">
          Traverse the ontology graph. Select a company or enter a key to explore
          connections.
        </p>
      </header>

      {/* Quick select: Company chips */}
      {companies && companies.items.length > 0 && (
        <div className="mb-8">
          <p className="text-[10px] font-bold text-secondary uppercase tracking-widest mb-3 font-label">
            Quick Select
          </p>
          <div className="flex flex-wrap gap-2">
            {companies.items
              .sort((a, b) => a.key.localeCompare(b.key))
              .slice(0, 30)
              .map((c) => {
                const name =
                  (c.properties.name as string) ?? c.key;
                return (
                  <button
                    key={c.key}
                    onClick={() => selectCompany(c.key)}
                    className={`px-3 py-1.5 text-[10px] font-label font-bold uppercase tracking-widest transition-all ${
                      activeRoot === c.key
                        ? "bg-primary text-surface"
                        : "bg-surface-container-high text-secondary border border-outline hover:text-on-surface hover:border-primary/50"
                    }`}
                  >
                    {name.length > 20 ? name.slice(0, 20) + "…" : name}
                  </button>
                );
              })}
          </div>
        </div>
      )}

      {/* Controls */}
      <form
        onSubmit={handleSubmit}
        className="flex items-end gap-4 mb-8"
      >
        <div className="flex-1 relative" ref={wrapperRef}>
          <label className="block text-[10px] font-bold text-secondary uppercase tracking-widest mb-3 font-label">
            Root Object Key
          </label>
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onFocus={() => suggestions.length > 0 && setShowSuggestions(true)}
            onKeyDown={handleKeyDown}
            placeholder="e.g. apple, google, microsoft"
            className="w-full bg-surface-container-high border-b-2 border-outline focus:border-primary py-3 px-4 text-sm text-on-surface outline-none transition-colors placeholder-secondary/50"
            autoComplete="off"
          />
          {showSuggestions && (
            <div className="absolute z-50 top-full left-0 right-0 mt-1 bg-surface-container border border-outline shadow-2xl shadow-black/40 max-h-[240px] overflow-y-auto">
              {suggestions.map((s, i) => (
                <button
                  key={s.key}
                  type="button"
                  onClick={() => { selectCompany(s.key); setShowSuggestions(false); }}
                  onMouseEnter={() => setActiveIdx(i)}
                  className={`w-full flex items-center gap-3 px-4 py-2.5 text-left transition-colors ${
                    i === activeIdx
                      ? "bg-surface-container-high text-on-surface"
                      : "text-secondary hover:bg-surface-container-high/50"
                  }`}
                >
                  <span className="material-symbols-outlined text-sm text-primary">
                    {s.type === "company" ? "domain" : s.type === "person" ? "person" : "category"}
                  </span>
                  <div className="min-w-0 flex-1">
                    <p className="text-sm font-medium truncate text-on-surface">{s.name}</p>
                    <p className="text-[10px] text-secondary font-label uppercase tracking-widest">{s.type} &middot; {s.key}</p>
                  </div>
                </button>
              ))}
            </div>
          )}
        </div>
        <div>
          <label className="block text-[10px] font-bold text-secondary uppercase tracking-widest mb-3 font-label">
            Depth
          </label>
          <select
            value={depth}
            onChange={(e) => setDepth(Number(e.target.value))}
            className="bg-surface-container-high border border-outline focus:border-primary py-3 px-4 text-sm text-on-surface font-label appearance-none cursor-pointer"
          >
            <option value={1}>1 hop</option>
            <option value={2}>2 hops</option>
            <option value={3}>3 hops</option>
          </select>
        </div>
        <button
          type="submit"
          className="px-8 py-3 bg-primary text-surface font-bold text-[11px] uppercase tracking-[0.2em] hover:bg-primary/80 active:scale-95 transition-all font-label"
        >
          Explore
        </button>
      </form>

      {/* Graph */}
      {isLoading && (
        <div className="h-[600px] flex items-center justify-center border border-outline bg-surface-container/30">
          <p className="text-secondary font-label text-sm uppercase tracking-widest animate-pulse">
            Loading graph...
          </p>
        </div>
      )}

      {error && (
        <div className="p-6 border border-red-500/30 bg-red-500/5 text-red-400 text-sm">
          Failed to load graph. Make sure the object key exists.
        </div>
      )}

      {data && !isLoading && (
        <div className="flex gap-0">
          <GraphFilterPanel
            filters={filters}
            setFilters={setFilters}
            stats={graphStats}
          />
          <div className="flex-1 min-w-0">
            <GraphView
              data={data}
              filters={filters}
              onNodeClick={(key, type) => setSelectedNode({ key, type })}
            />
          </div>
          {selectedNode && (
            <NodeDetailPanel
              nodeKey={selectedNode.key}
              nodeType={selectedNode.type}
              onClose={() => setSelectedNode(null)}
              onNavigate={(key) => {
                selectCompany(key);
                setSelectedNode(null);
              }}
            />
          )}
        </div>
      )}

      {!activeRoot && !isLoading && (
        <div className="h-[600px] flex items-center justify-center border border-outline bg-surface-container/30">
          <p className="text-secondary font-label text-sm uppercase tracking-widest">
            Select a company above or enter a key
          </p>
        </div>
      )}
    </div>
  );
}
