"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import { useRouter, useSearchParams, usePathname } from "next/navigation";
import Link from "next/link";
import { Search, X, ExternalLink, Calendar, Tag, Filter, Loader2 } from "lucide-react";
import { useTranslation } from "../lib/i18n";
import { trackEvent } from "../lib/analytics";
import { getSourceMeta } from "../lib/sources";

export type SearchIndexItem = {
  id: string;
  title: string;
  url: string;
  description: string;
  source: string;
  score: number;
  comments: number;
  date: string;
  tags: string[];
  hasDetail: boolean;
};

type SearchIndex = {
  generated_at: string;
  total: number;
  items: SearchIndexItem[];
};

export function SearchClient({
  fallbackItems,
}: {
  fallbackItems?: SearchIndexItem[];
}) {
  const { t } = useTranslation();
  const router = useRouter();
  const pathname = usePathname();
  const searchParams = useSearchParams();

  const [index, setIndex] = useState<SearchIndex | null>(
    fallbackItems ? { generated_at: "", total: fallbackItems.length, items: fallbackItems } : null
  );
  const [loading, setLoading] = useState(!fallbackItems);
  const [error, setError] = useState<string | null>(null);

  const [query, setQuery] = useState(searchParams.get("q") ?? "");
  const [source, setSource] = useState(searchParams.get("source") ?? "all");
  const [date, setDate] = useState(searchParams.get("date") ?? "all");
  const [tag, setTag] = useState(searchParams.get("tag") ?? "all");

  useEffect(() => {
    if (fallbackItems) return;
    let cancelled = false;
    fetch("/search-index.json")
      .then((res) => {
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        return res.json();
      })
      .then((data: SearchIndex) => {
        if (!cancelled) {
          setIndex(data);
          setLoading(false);
        }
      })
      .catch((err) => {
        if (!cancelled) {
          setError(err instanceof Error ? err.message : "Unknown error");
          setLoading(false);
        }
      });
    return () => {
      cancelled = true;
    };
  }, [fallbackItems]);

  const updateUrl = useCallback(
    (params: { q?: string; source?: string; date?: string; tag?: string }) => {
      const sp = new URLSearchParams(searchParams.toString());
      for (const [key, value] of Object.entries(params)) {
        if (!value || value === "all") {
          sp.delete(key);
        } else {
          sp.set(key, value);
        }
      }
      const qs = sp.toString();
      router.replace(`${pathname}${qs ? `?${qs}` : ""}`, { scroll: false });
    },
    [pathname, router, searchParams]
  );

  const items = useMemo(() => index?.items ?? [], [index]);

  const sources = useMemo(
    () => Array.from(new Set(items.map((i) => i.source))).sort(),
    [items]
  );
  const dates = useMemo(
    () => Array.from(new Set(items.map((i) => i.date))).filter(Boolean).sort().reverse(),
    [items]
  );
  const tags = useMemo(
    () => Array.from(new Set(items.flatMap((i) => i.tags))).filter(Boolean).sort(),
    [items]
  );

  const filtered = useMemo(() => {
    const q = query.trim().toLowerCase();
    return items.filter((item) => {
      if (source !== "all" && item.source !== source) return false;
      if (date !== "all" && item.date !== date) return false;
      if (tag !== "all" && !item.tags.includes(tag)) return false;
      if (!q) return true;
      const hay = `${item.title} ${item.description} ${item.tags.join(" ")}`.toLowerCase();
      return hay.includes(q);
    });
  }, [items, query, source, date, tag]);

  useEffect(() => {
    const timeout = setTimeout(() => {
      updateUrl({ q: query });
      if (query.trim()) {
        trackEvent("search", {
          query: query.trim(),
          source,
          date,
          tag,
          results: filtered.length,
        });
      }
    }, 500);
    return () => clearTimeout(timeout);
  }, [query, source, date, tag, updateUrl, filtered.length]);

  const activeFilters = [source, date, tag].filter((v) => v !== "all").length;

  if (loading) {
    return (
      <div className="py-16 flex flex-col items-center gap-3 text-text-muted">
        <Loader2 className="h-6 w-6 animate-spin" />
        <p>{t("search.loading")}</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="py-16 text-center text-text-muted">
        <p className="text-lg">{t("search.error")}</p>
        <p className="text-sm mt-1">{error}</p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Search input */}
      <div className="relative">
        <Search className="absolute left-4 top-1/2 -translate-y-1/2 h-5 w-5 text-text-dim" />
        <input
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder={t("search.placeholder")}
          className="w-full pl-11 pr-10 py-3.5 rounded-xl bg-surface-card border border-surface-border text-text-primary placeholder:text-text-dim focus:outline-none focus:ring-2 focus:ring-accent-violet/30 focus:border-accent-violet/50"
        />
        {query && (
          <button
            onClick={() => setQuery("")}
            className="absolute right-4 top-1/2 -translate-y-1/2 text-text-dim hover:text-text-primary"
            aria-label={t("search.clear")}
          >
            <X className="h-4 w-4" />
          </button>
        )}
      </div>

      {/* Filters */}
      <div className="flex flex-col sm:flex-row gap-3">
        <div className="flex items-center gap-2 text-sm text-text-dim">
          <Filter className="h-4 w-4" />
          <span>{t("search.filters")}</span>
          {activeFilters > 0 && (
            <span className="px-1.5 py-0.5 rounded-full bg-accent-violet/10 text-accent-violet text-xs font-semibold">
              {activeFilters}
            </span>
          )}
        </div>

        <select
          value={source}
          onChange={(e) => {
            setSource(e.target.value);
            updateUrl({ source: e.target.value });
          }}
          className="flex-1 px-3 py-2 rounded-lg bg-surface-card border border-surface-border text-sm text-text-primary focus:outline-none focus:border-accent-violet/50"
        >
          <option value="all">{t("search.allSources")}</option>
          {sources.map((s) => {
            const meta = getSourceMeta(s);
            return (
              <option key={s} value={s}>
                {meta.shortLabel}
              </option>
            );
          })}
        </select>

        <select
          value={date}
          onChange={(e) => {
            setDate(e.target.value);
            updateUrl({ date: e.target.value });
          }}
          className="flex-1 px-3 py-2 rounded-lg bg-surface-card border border-surface-border text-sm text-text-primary focus:outline-none focus:border-accent-violet/50"
        >
          <option value="all">{t("search.allDates")}</option>
          {dates.map((d) => (
            <option key={d} value={d}>
              {d}
            </option>
          ))}
        </select>

        <select
          value={tag}
          onChange={(e) => {
            setTag(e.target.value);
            updateUrl({ tag: e.target.value });
          }}
          className="flex-1 px-3 py-2 rounded-lg bg-surface-card border border-surface-border text-sm text-text-primary focus:outline-none focus:border-accent-violet/50"
        >
          <option value="all">{t("search.allTags")}</option>
          {tags.map((t) => (
            <option key={t} value={t}>
              {t}
            </option>
          ))}
        </select>
      </div>

      {/* Results count */}
      <div className="text-sm text-text-muted">
        {t("search.resultsCount", { count: filtered.length })}
      </div>

      {/* Results */}
      <div className="space-y-3">
        {filtered.map((item) => {
          const meta = getSourceMeta(item.source);
          const detailUrl = `/item/${item.id}/`;
          const titleLink = item.hasDetail ? detailUrl : item.url;
          return (
            <article
              key={item.id}
              className="group p-4 rounded-xl bg-surface-card border border-surface-border hover:border-accent-violet/30 hover:shadow-sm transition-all"
            >
              <div className="flex items-start justify-between gap-3">
                <div className="flex-1 min-w-0">
                  <h3 className="font-semibold text-text-primary group-hover:text-accent-violet transition-colors">
                    {item.hasDetail ? (
                      <Link href={titleLink} className="hover:underline underline-offset-2">
                        {item.title}
                      </Link>
                    ) : (
                      <a
                        href={titleLink}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="hover:underline underline-offset-2"
                      >
                        {item.title}
                      </a>
                    )}
                  </h3>
                  <p className="mt-1 text-sm text-text-secondary line-clamp-2">{item.description}</p>
                  <div className="mt-2 flex items-center gap-2 flex-wrap text-xs text-text-dim">
                    <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-md border ${meta.bg} ${meta.color} border-current/10`}>
                      {meta.icon}
                      {meta.shortLabel}
                    </span>
                    <span className="inline-flex items-center gap-1">
                      <Calendar className="h-3 w-3" />
                      {item.date}
                    </span>
                    {item.tags.length > 0 && (
                      <span className="inline-flex items-center gap-1">
                        <Tag className="h-3 w-3" />
                        {item.tags.slice(0, 3).join(", ")}
                      </span>
                    )}
                  </div>
                </div>
                <a
                  href={item.url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-text-dim hover:text-text-primary p-2 shrink-0"
                  title={t("search.openOriginal")}
                >
                  <ExternalLink className="h-4 w-4" />
                </a>
              </div>
            </article>
          );
        })}
      </div>

      {filtered.length === 0 && (
        <div className="text-center py-16 text-text-muted">
          <p className="text-lg">{t("search.emptyTitle")}</p>
          <p className="text-sm mt-1">{t("search.emptyHint")}</p>
        </div>
      )}
    </div>
  );
}
