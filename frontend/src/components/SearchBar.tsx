import { useState, useEffect, useRef } from "react";
import { useNavigate } from "react-router-dom";
import { api } from "@/lib/api";

const TYPE_ICONS: Record<string, string> = {
  company: "domain",
  person: "person",
  article: "article",
  repository: "code",
  event: "event",
};

interface Suggestion {
  key: string;
  type: string;
  name: string;
}

export function SearchBar() {
  const [query, setQuery] = useState("");
  const [suggestions, setSuggestions] = useState<Suggestion[]>([]);
  const [showDropdown, setShowDropdown] = useState(false);
  const [activeIndex, setActiveIndex] = useState(-1);
  const navigate = useNavigate();
  const wrapperRef = useRef<HTMLDivElement>(null);
  const debounceRef = useRef<ReturnType<typeof setTimeout>>();

  // Fetch suggestions on input change
  useEffect(() => {
    if (query.trim().length < 1) {
      setSuggestions([]);
      setShowDropdown(false);
      return;
    }

    clearTimeout(debounceRef.current);
    debounceRef.current = setTimeout(async () => {
      try {
        const results = await api.suggest(query.trim());
        setSuggestions(results);
        setShowDropdown(results.length > 0);
        setActiveIndex(-1);
      } catch {
        setSuggestions([]);
      }
    }, 150);

    return () => clearTimeout(debounceRef.current);
  }, [query]);

  // Close dropdown on outside click
  useEffect(() => {
    const handler = (e: MouseEvent) => {
      if (wrapperRef.current && !wrapperRef.current.contains(e.target as Node)) {
        setShowDropdown(false);
      }
    };
    document.addEventListener("mousedown", handler);
    return () => document.removeEventListener("mousedown", handler);
  }, []);

  const navigateTo = (suggestion: Suggestion) => {
    setShowDropdown(false);
    setQuery("");
    if (suggestion.type === "company") {
      navigate(`/company/${suggestion.key}`);
    } else {
      navigate(`/graph/${suggestion.key}`);
    }
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (activeIndex >= 0 && suggestions[activeIndex]) {
      navigateTo(suggestions[activeIndex]);
    } else if (query.trim()) {
      setShowDropdown(false);
      navigate(`/search?q=${encodeURIComponent(query.trim())}`);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (!showDropdown) return;
    if (e.key === "ArrowDown") {
      e.preventDefault();
      setActiveIndex((i) => Math.min(i + 1, suggestions.length - 1));
    } else if (e.key === "ArrowUp") {
      e.preventDefault();
      setActiveIndex((i) => Math.max(i - 1, -1));
    } else if (e.key === "Escape") {
      setShowDropdown(false);
    }
  };

  return (
    <div ref={wrapperRef} className="relative">
      <form onSubmit={handleSubmit}>
        <span className="material-symbols-outlined absolute left-3 top-1/2 -translate-y-1/2 text-secondary">
          search
        </span>
        <input
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onFocus={() => suggestions.length > 0 && setShowDropdown(true)}
          onKeyDown={handleKeyDown}
          placeholder="Search objects..."
          className="w-full bg-surface-container-high border-b-2 border-outline focus:border-primary pl-10 pr-4 py-3 text-sm text-on-surface outline-none transition-colors placeholder-secondary/50 font-body"
          autoComplete="off"
        />
      </form>

      {/* Dropdown */}
      {showDropdown && (
        <div className="absolute z-50 top-full left-0 right-0 mt-1 bg-surface-container border border-outline backdrop-blur-md shadow-2xl shadow-black/40 max-h-[320px] overflow-y-auto">
          {suggestions.map((s, i) => (
            <button
              key={s.key}
              onClick={() => navigateTo(s)}
              onMouseEnter={() => setActiveIndex(i)}
              className={`w-full flex items-center gap-3 px-4 py-3 text-left transition-colors ${
                i === activeIndex
                  ? "bg-surface-container-high text-on-surface"
                  : "text-secondary hover:bg-surface-container-high/50 hover:text-on-surface"
              }`}
            >
              <span className="material-symbols-outlined text-sm text-primary">
                {TYPE_ICONS[s.type] ?? "category"}
              </span>
              <div className="min-w-0 flex-1">
                <p className="text-sm font-medium truncate text-on-surface">
                  {highlightMatch(s.name, query)}
                </p>
                <p className="text-[10px] text-secondary font-label uppercase tracking-widest">
                  {s.type} &middot; {s.key}
                </p>
              </div>
              <span className="material-symbols-outlined text-sm text-secondary/30">
                arrow_forward
              </span>
            </button>
          ))}
        </div>
      )}
    </div>
  );
}

/** Highlight matching substring in bold */
function highlightMatch(text: string, query: string) {
  if (!query) return text;
  const idx = text.toLowerCase().indexOf(query.toLowerCase());
  if (idx === -1) return text;
  return (
    <>
      {text.slice(0, idx)}
      <strong className="text-primary font-bold">
        {text.slice(idx, idx + query.length)}
      </strong>
      {text.slice(idx + query.length)}
    </>
  );
}
