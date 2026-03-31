import { Link } from "react-router-dom";
import { SourceBadge } from "./SourceBadge";
import type { OntologyObject } from "@/lib/api";

interface ObjectCardProps {
  object: OntologyObject;
}

const TYPE_ICONS: Record<string, string> = {
  company: "domain",
  person: "person",
  article: "article",
  repository: "code",
  event: "event",
};

export function ObjectCard({ object }: ObjectCardProps) {
  const name = (object.properties.name as string) ?? object.key;
  const icon = TYPE_ICONS[object.type] ?? "category";
  const sources = Object.keys(object.sources);
  const linkTo =
    object.type === "company"
      ? `/company/${object.key}`
      : `/graph/${object.key}`;

  return (
    <Link
      to={linkTo}
      className="block bg-surface-container/50 backdrop-blur-sm border border-outline p-6 hover:border-primary/50 transition-all group"
    >
      <div className="flex items-start justify-between mb-3">
        <div className="flex items-center gap-3">
          <span className="material-symbols-outlined text-primary">{icon}</span>
          <div>
            <h3 className="font-headline font-bold text-on-surface text-sm tracking-tight group-hover:text-primary transition-colors">
              {name}
            </h3>
            <p className="text-[10px] text-secondary uppercase tracking-widest font-label">
              {object.type} &middot; {object.key}
            </p>
          </div>
        </div>
      </div>

      {object.properties.description && (
        <p className="text-xs text-on-surface-variant leading-relaxed mb-4 line-clamp-2">
          {object.properties.description as string}
        </p>
      )}

      <div className="flex flex-wrap gap-1">
        {sources.map((s) => (
          <SourceBadge key={s} source={s} />
        ))}
      </div>
    </Link>
  );
}
