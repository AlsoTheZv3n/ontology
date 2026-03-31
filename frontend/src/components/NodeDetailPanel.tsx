import { useObject, useObjectLinks } from "@/hooks/useOntology";
import { SourceBadge } from "./SourceBadge";
import { Link } from "react-router-dom";

interface Props {
  nodeKey: string;
  nodeType: string;
  onClose: () => void;
  onNavigate: (key: string) => void;
}

export function NodeDetailPanel({ nodeKey, nodeType, onClose, onNavigate }: Props) {
  const { data, isLoading } = useObject(nodeKey);
  const { data: links } = useObjectLinks(nodeKey);

  const props = (data?.properties ?? {}) as Record<string, unknown>;
  const sources = data?.sources
    ? Object.keys(data.sources as Record<string, unknown>)
    : [];

  if (isLoading) {
    return (
      <div className="w-80 flex-shrink-0 bg-surface-container border-l border-outline p-4">
        <div className="animate-pulse space-y-3">
          <div className="h-4 bg-surface-container-high w-2/3" />
          <div className="h-20 bg-surface-container-high" />
        </div>
      </div>
    );
  }

  const SKIP_KEYS = new Set(["missing_sources", "source_coverage", "innovation_score"]);

  return (
    <div className="w-80 flex-shrink-0 bg-surface-container border-l border-outline overflow-y-auto max-h-[640px]">
      {/* Header */}
      <div className="flex items-center justify-between p-4 border-b border-outline">
        <div className="min-w-0 flex-1">
          <span className="text-[10px] text-primary font-label uppercase tracking-widest">
            {nodeType}
          </span>
          <h3 className="text-sm font-headline font-bold text-on-surface mt-0.5 truncate">
            {(props.name as string) ?? nodeKey}
          </h3>
        </div>
        <button
          onClick={onClose}
          className="text-secondary hover:text-on-surface ml-2 flex-shrink-0"
        >
          <span className="material-symbols-outlined text-sm">close</span>
        </button>
      </div>

      {/* Sources */}
      {sources.length > 0 && (
        <div className="px-4 pt-3 flex flex-wrap gap-1">
          {sources.map((s) => (
            <SourceBadge key={s} source={s} />
          ))}
        </div>
      )}

      {/* Properties */}
      <div className="p-4 space-y-2.5">
        {Object.entries(props)
          .filter(([k, v]) => v != null && v !== "" && !SKIP_KEYS.has(k) && k !== "name")
          .slice(0, 15)
          .map(([key, value]) => (
            <div key={key}>
              <span className="text-[9px] text-secondary uppercase tracking-widest font-label">
                {key.replace(/_/g, " ")}
              </span>
              <p className="text-xs text-on-surface mt-0.5 break-words">
                {typeof value === "number"
                  ? value > 1e9
                    ? `$${(value / 1e9).toFixed(1)}B`
                    : value > 1e6
                      ? `$${(value / 1e6).toFixed(1)}M`
                      : value.toLocaleString()
                  : Array.isArray(value)
                    ? value.join(", ")
                    : String(value).slice(0, 200)}
              </p>
            </div>
          ))}
      </div>

      {/* Connections */}
      {links && (links as unknown[]).length > 0 && (
        <div className="p-4 border-t border-outline">
          <p className="text-[10px] text-secondary uppercase tracking-widest font-label mb-2">
            Connections ({(links as unknown[]).length})
          </p>
          <div className="space-y-1.5 max-h-[200px] overflow-y-auto">
            {(links as Array<Record<string, unknown>>).slice(0, 30).map((l, i) => {
              const isFrom = (l.from_key as string) === nodeKey;
              const targetKey = isFrom ? (l.to_key as string) : (l.from_key as string);
              const targetLabel = isFrom ? (l.to_label as string) : (l.from_label as string);
              const targetType = isFrom ? (l.to_type as string) : (l.from_type as string);
              return (
                <button
                  key={i}
                  onClick={() => onNavigate(targetKey)}
                  className="w-full flex items-center justify-between py-1.5 text-left hover:bg-surface-container-high/50 px-1 -mx-1 transition-colors"
                >
                  <div className="min-w-0 flex-1">
                    <p className="text-xs text-on-surface truncate">{targetLabel || targetKey}</p>
                    <p className="text-[9px] text-secondary uppercase tracking-widest">
                      {(l.type as string).replace(/_/g, " ")} · {targetType}
                    </p>
                  </div>
                  <span className="material-symbols-outlined text-xs text-secondary/30">
                    arrow_forward
                  </span>
                </button>
              );
            })}
          </div>
        </div>
      )}

      {/* Actions */}
      <div className="p-4 border-t border-outline space-y-2">
        <Link
          to={nodeType === "company" ? `/company/${nodeKey}` : `/graph/${nodeKey}`}
          className="block w-full text-center text-[10px] font-label font-bold uppercase tracking-widest py-2 border border-outline hover:border-primary/50 text-secondary hover:text-on-surface transition-all"
        >
          View Full Detail
        </Link>
      </div>
    </div>
  );
}
