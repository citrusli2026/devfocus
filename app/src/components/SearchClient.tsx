"use client";

import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { useRouter, useSearchParams, usePathname } from "next/navigation";
import Link from "next/link";
import MiniSearch from "minisearch";
import { Search, X, ExternalLink, Calendar, Tag, Filter, ChevronDown } from "lucide-react";
import { useTranslation } from "../lib/i18n";
import { trackEvent } from "../lib/analytics";
import { getSourceMeta } from "../lib/sources";
import { EmptyState } from "./EmptyState";

const PAGE_SIZE = 20;

export type SearchIndexItem = {
  id: string;
  title: string;
  url: string;
  description: string;
  source: string;
  domain: string;
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

  const inputRef = useRef<HTMLInputElement>(null);

  const [query, setQuery] = useState(searchParams.get("q") ?? "");
  const [source, setSource] = useState(searchParams.get("source") ?? "all");
  const [date, setDate] = useState(searchParams.get("date") ?? "all");
  const [tag, setTag] = useState(searchParams.get("tag") ?? "all");
  const [domain, setDomain] = useState(searchParams.get("domain") ?? "all");
  const [visibleCount, setVisibleCount] = useState(PAGE_SIZE);

  useEffect(() => {
    if (searchParams.get("focus") === "1" && inputRef.current) {
      inputRef.current.focus();
      const sp = new URLSearchParams(searchParams.toString());
      sp.delete("focus");
      const qs = sp.toString();
      router.replace(`${pathname}${qs ? `?${qs}` : ""}`, { scroll: false });
    }
  }, [searchParams, pathname, router]);

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
    (params: { q?: string; source?: string; date?: string; tag?: string; domain?: string }) => {
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
  const domains = useMemo(
    () => Array.from(new Set(items.map((i) => i.domain))).filter(Boolean).sort(),
    [items]
  );

  const miniSearch = useMemo(() => {
    const ms = new MiniSearch<SearchIndexItem>({
      fields: ["title", "description", "tags", "domain"],
      storeFields: [],
      searchOptions: {
        boost: { title: 4, tags: 3, domain: 2, description: 1 },
        fuzzy: 0.2,
        prefix: true,
      },
    });
    ms.addAll(items);
    return ms;
  }, [items]);

  const filtered = useMemo(() => {
    const q = query.trim();
    let candidates = items;
    let scored = false;

    if (q) {
      const raw = miniSearch.search(q, { prefix: true, fuzzy: 0.2 });
      const itemById = new Map(items.map((i) => [i.id, i]));
      candidates = raw
        .map((r) => itemById.get(r.id))
        .filter((i): i is SearchIndexItem => i !== undefined);
      scored = true;
    }

    const out = candidates.filter((item) => {
      if (source !== "all" && item.source !== source) return false;
      if (date !== "all" && item.date !== date) return false;
      if (tag !== "all" && !item.tags.includes(tag)) return false;
      if (domain !== "all" && item.domain !== domain) return false;
      return true;
    });

    if (!scored) {
      // No query: sort by date desc, then score desc
      out.sort((a, b) => {
        const dateCmp = b.date.localeCompare(a.date);
        if (dateCmp !== 0) return dateCmp;
        return b.score - a.score;
      });
    }
    return out;
  }, [items, miniSearch, query, source, date, tag, domain]);

  useEffect(() => {
    const timeout = setTimeout(() => {
      updateUrl({ q: query });
      if (query.trim()) {
        trackEvent("search", {
          query: query.trim(),
          source,
          date,
          tag,
          domain,
          results: filtered.length,
        });
      }
    }, 500);
    return () => clearTimeout(timeout);
  }, [query, source, date, tag, domain, updateUrl, filtered.length]);

  const visibleResults = filtered.slice(0, visibleCount);
  const hasMore = visibleCount < filtered.length;

  const activeFilters = [source, date, tag, domain].filter((v) => v !== "all").length;

  if (loading) {
    return (
      <div className="space-y-5 animate-pulse">
        <div className="h-12 rounded-xl bg-surface-hover" />
        <div className="flex flex-col sm:flex-row gap-3">
          <div className="h-10 rounded-lg bg-surface-hover flex-[2]" />
          <div className="h-10 rounded-lg bg-surface-hover flex-1" />
          <div className="h-10 rounded-lg bg-surface-hover flex-1" />
          <div className="h-10 rounded-lg bg-surface-hover flex-1" />
        </div>
        <div className="h-4 w-32 rounded bg-surface-hover" />
        <div className="space-y-3">
          {Array.from({ length: 6 }).map((_, i) => (
            <div key={i} className="h-24 rounded-xl bg-surface-hover" />
          ))}
        </div>
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
          ref={inputRef}
          type="text"
          value={query}
          onChange={(e) => {
            setVisibleCount(PAGE_SIZE);
            setQuery(e.target.value);
          }}
          placeholder={t("search.placeholder")}
          className="w-full pl-11 pr-10 py-3.5 rounded-xl bg-surface-card border border-surface-border text-text-primary placeholder:text-text-dim focus:outline-none focus:ring-2 focus:ring-accent-violet/30 focus:border-accent-violet/50"
        />
        {query && (
          <button
            onClick={() => {
              setVisibleCount(PAGE_SIZE);
              setQuery("");
            }}
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
            setVisibleCount(PAGE_SIZE);
            setSource(e.target.value);
            updateUrl({ source: e.target.value });
          }}
          aria-label={t("search.allSources")}
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
            setVisibleCount(PAGE_SIZE);
            setDate(e.target.value);
            updateUrl({ date: e.target.value });
          }}
          aria-label={t("search.allDates")}
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
            setVisibleCount(PAGE_SIZE);
            setTag(e.target.value);
            updateUrl({ tag: e.target.value });
          }}
          aria-label={t("search.allTags")}
          className="flex-1 px-3 py-2 rounded-lg bg-surface-card border border-surface-border text-sm text-text-primary focus:outline-none focus:border-accent-violet/50"
        >
          <option value="all">{t("search.allTags")}</option>
          {tags.map((t) => (
            <option key={t} value={t}>
              {t}
            </option>
          ))}
        </select>

        <select
          value={domain}
          onChange={(e) => {
            setVisibleCount(PAGE_SIZE);
            setDomain(e.target.value);
            updateUrl({ domain: e.target.value });
          }}
          aria-label={t("search.allDomains")}
          className="flex-1 px-3 py-2 rounded-lg bg-surface-card border border-surface-border text-sm text-text-primary focus:outline-none focus:border-accent-violet/50"
        >
          <option value="all">{t("search.allDomains")}</option>
          {domains.map((d) => (
            <option key={d} value={d}>
              {d}
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
        {visibleResults.map((item) => {
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
                  <h3 className="font-semibold text-text-primary group-hover:text-accent-violet transition-colors break-words">
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
        <EmptyState title={t("search.emptyTitle")} hint={t("search.emptyHint")} icon="search" />
      )}

      {hasMore && (
        <div className="pt-2 text-center">
          <button
            onClick={() => setVisibleCount((c) => c + PAGE_SIZE)}
            className="inline-flex items-center gap-1.5 px-5 py-2.5 rounded-xl bg-surface-card border border-surface-border text-sm font-semibold text-text-secondary hover:border-accent-violet/30 hover:text-accent-violet transition-colors"
          >
            {t("search.loadMore")}
            <ChevronDown className="h-4 w-4" />
          </button>
        </div>
      )}
    </div>
  );
}
