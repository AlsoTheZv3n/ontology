import { useEffect, useState } from "react";

interface SchemaData {
  object_types: { type: string; count: number }[];
  link_types: {
    from_type: string;
    type: string;
    to_type: string;
    count: number;
  }[];
}

const TYPE_COLORS: Record<string, { bg: string; text: string; border: string }> = {
  company:         { bg: "bg-indigo-500/20",  text: "text-indigo-400",  border: "border-indigo-500/30" },
  person:          { bg: "bg-sky-500/20",     text: "text-sky-400",     border: "border-sky-500/30" },
  article:         { bg: "bg-orange-500/20",  text: "text-orange-400",  border: "border-orange-500/30" },
  repository:      { bg: "bg-emerald-500/20", text: "text-emerald-400", border: "border-emerald-500/30" },
  event:           { bg: "bg-purple-500/20",  text: "text-purple-400",  border: "border-purple-500/30" },
  country:         { bg: "bg-amber-500/20",   text: "text-amber-400",   border: "border-amber-500/30" },
  macro_indicator: { bg: "bg-teal-500/20",    text: "text-teal-400",    border: "border-teal-500/30" },
};

function typeStyle(t: string) {
  return TYPE_COLORS[t] ?? { bg: "bg-slate-500/20", text: "text-slate-400", border: "border-slate-500/30" };
}

function TypeBadge({ type }: { type: string }) {
  const s = typeStyle(type);
  return (
    <span
      className={`inline-block px-2 py-0.5 text-[10px] font-label font-bold uppercase tracking-widest border ${s.bg} ${s.text} ${s.border}`}
    >
      {type.replace("_", " ")}
    </span>
  );
}

export function Schema() {
  const [data, setData] = useState<SchemaData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetch("/api/insights/schema")
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

  return (
    <div>
      {/* Header */}
      <header className="mb-12 border-l-2 border-primary pl-8">
        <div className="flex items-center gap-2 text-primary font-label text-xs font-bold uppercase tracking-[0.2em] mb-4">
          <span className="w-2 h-2 bg-primary rounded-full animate-pulse" />
          Data Model
        </div>
        <h2 className="text-5xl font-bold tracking-tighter text-on-surface mb-4 font-headline">
          Ontology Schema
        </h2>
        <p className="text-on-surface-variant max-w-2xl text-lg font-light leading-relaxed">
          Object types and link types that define the knowledge graph structure.
        </p>
      </header>

      {loading && (
        <p className="text-sm text-secondary font-label">Loading schema...</p>
      )}
      {error && (
        <p className="text-sm text-red-400 font-label">Error: {error}</p>
      )}

      {!loading && !error && data && (
        <>
          {/* Object Types */}
          <section className="mb-10">
            <div className="flex items-center gap-2 mb-4">
              <span className="material-symbols-outlined text-sm text-primary">category</span>
              <h3 className="text-[10px] uppercase tracking-[0.3em] font-bold text-primary font-label">
                Object Types
              </h3>
            </div>

            <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
              {(data.object_types ?? []).map((ot) => {
                const s = typeStyle(ot.type);
                return (
                  <div
                    key={ot.type}
                    className={`p-5 border ${s.border} ${s.bg} backdrop-blur-sm`}
                  >
                    <p className={`text-xs font-label font-bold uppercase tracking-widest ${s.text} mb-2`}>
                      {ot.type.replace("_", " ")}
                    </p>
                    <p className="text-3xl font-headline font-bold tracking-tighter text-on-surface">
                      {ot.count.toLocaleString()}
                    </p>
                  </div>
                );
              })}
            </div>
          </section>

          {/* Link Types */}
          <section>
            <div className="flex items-center gap-2 mb-4">
              <span className="material-symbols-outlined text-sm text-primary">link</span>
              <h3 className="text-[10px] uppercase tracking-[0.3em] font-bold text-primary font-label">
                Link Types
              </h3>
            </div>

            {(data.link_types ?? []).length === 0 ? (
              <div className="bg-surface-container/50 border border-outline p-6 text-center">
                <p className="text-sm text-secondary">No link types defined.</p>
              </div>
            ) : (
              <div className="bg-surface-container/50 border border-outline overflow-hidden">
                <table className="w-full">
                  <thead>
                    <tr className="border-b border-outline">
                      <th className="text-left text-[10px] font-label font-bold uppercase tracking-widest text-secondary px-4 py-3">
                        From
                      </th>
                      <th className="text-center text-[10px] font-label font-bold uppercase tracking-widest text-secondary px-4 py-3">
                        Relationship
                      </th>
                      <th className="text-left text-[10px] font-label font-bold uppercase tracking-widest text-secondary px-4 py-3">
                        To
                      </th>
                      <th className="text-right text-[10px] font-label font-bold uppercase tracking-widest text-secondary px-4 py-3">
                        Count
                      </th>
                    </tr>
                  </thead>
                  <tbody>
                    {data.link_types.map((lt, i) => (
                      <tr
                        key={`${lt.from_type}-${lt.type}-${lt.to_type}-${i}`}
                        className="border-b border-outline/50 hover:bg-surface-container-high/30 transition-colors"
                      >
                        <td className="px-4 py-3">
                          <TypeBadge type={lt.from_type} />
                        </td>
                        <td className="px-4 py-3 text-center">
                          <span className="text-secondary mx-2">-</span>
                          <span className="text-xs text-on-surface font-label font-bold uppercase tracking-widest">
                            {lt.type.replace("_", " ")}
                          </span>
                          <span className="text-secondary mx-2">-</span>
                        </td>
                        <td className="px-4 py-3">
                          <TypeBadge type={lt.to_type} />
                        </td>
                        <td className="px-4 py-3 text-right text-sm font-headline font-bold text-on-surface">
                          {lt.count.toLocaleString()}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </section>
        </>
      )}
    </div>
  );
}
