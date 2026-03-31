import { useState, useEffect } from "react";
import { useSearchParams } from "react-router-dom";
import { useSearch } from "@/hooks/useOntology";
import { ObjectCard } from "@/components/ObjectCard";
import { SearchBar } from "@/components/SearchBar";

const TYPES = ["all", "company", "person", "article", "repository", "event"];

export function Search() {
  const [searchParams] = useSearchParams();
  const qParam = searchParams.get("q") ?? "";
  const [query, setQuery] = useState(qParam);
  const [typeFilter, setTypeFilter] = useState("all");

  useEffect(() => {
    if (qParam) setQuery(qParam);
  }, [qParam]);

  const activeType = typeFilter === "all" ? undefined : typeFilter;
  const { data: results, isLoading } = useSearch(query, activeType);

  return (
    <div>
      <header className="mb-12 border-l-2 border-primary pl-8">
        <h2 className="text-5xl font-bold tracking-tighter text-on-surface mb-4 font-headline">
          Search
        </h2>
        <p className="text-on-surface-variant max-w-2xl text-lg font-light leading-relaxed">
          Full-text search across all ontology objects.
        </p>
      </header>

      <div className="max-w-2xl mb-8">
        <SearchBar />
      </div>

      {/* Type filter chips */}
      <div className="flex gap-2 mb-8">
        {TYPES.map((t) => (
          <button
            key={t}
            onClick={() => setTypeFilter(t)}
            className={`px-4 py-2 text-[10px] font-label font-bold uppercase tracking-widest transition-all ${
              typeFilter === t
                ? "bg-primary text-surface"
                : "bg-surface-container-high text-secondary border border-outline hover:text-on-surface"
            }`}
          >
            {t}
          </button>
        ))}
      </div>

      {/* Results */}
      {isLoading && query && (
        <div className="animate-pulse space-y-4">
          {[1, 2, 3].map((i) => (
            <div key={i} className="h-24 bg-surface-container-high" />
          ))}
        </div>
      )}

      {results && (
        <>
          <p className="text-[10px] text-secondary font-label uppercase tracking-widest mb-6">
            {results.length} results for &ldquo;{query}&rdquo;
          </p>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {results.map((obj) => (
              <ObjectCard key={obj.id} object={obj} />
            ))}
          </div>
        </>
      )}

      {!query && (
        <div className="h-64 flex items-center justify-center border border-outline bg-surface-container/30">
          <p className="text-secondary font-label text-sm uppercase tracking-widest">
            Enter a search term above
          </p>
        </div>
      )}
    </div>
  );
}
