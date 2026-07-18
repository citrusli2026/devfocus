"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import { Digest, FeedItem } from "../types";
import { FeedList } from "../components/FeedCard";
import { RelativeTime } from "../components/RelativeTime";
import { SubscribeForm } from "../components/SubscribeForm";
import { EmptyState } from "../components/EmptyState";
import { useTranslation } from "../lib/i18n";
import { useReadItems } from "../lib/read-items";
import { trackEvent } from "../lib/analytics";
import { SOURCE_ORDER, getSourceMeta } from "../lib/sources";
import Link from "next/link";
import { TrendingUp, Calendar, History, CheckCheck } from "lucide-react";
import digestData from "../data/digest.json";

export default function Home() {
  const { t, locale } = useTranslation();
  const { markAllAsRead, isRead } = useReadItems();
  const digest = digestData as Digest;
  const [active, setActive] = useState<string>("all");
  const tabsRef = useRef<HTMLDivElement>(null);
  const [scrollState, setScrollState] = useState({ left: false, right: false });

  const allItems = digest.daily.items;
  const readCount = allItems.filter((i) => isRead(i.id)).length;

  const { activeSources, itemsBySource } = useMemo(() => {
    const presentSources = Array.from(new Set(allItems.map((i) => i.source)));
    const ordered = SOURCE_ORDER.filter((s) => presentSources.includes(s));
    const remaining = presentSources.filter((s) => !SOURCE_ORDER.includes(s));
    const bySource: Record<string, FeedItem[]> = {};
    for (const src of [...ordered, ...remaining]) {
      bySource[src] = allItems.filter((i) => i.source === src);
    }
    return { activeSources: ordered.concat(remaining), itemsBySource: bySource };
  }, [allItems]);

  useEffect(() => {
    const el = tabsRef.current;
    if (!el) return;
    const update = () => {
      setScrollState({
        left: el.scrollLeft > 4,
        right: el.scrollLeft + el.clientWidth < el.scrollWidth - 4,
      });
    };
    update();
    el.addEventListener("scroll", update, { passive: true });
    window.addEventListener("resize", update);
    return () => {
      el.removeEventListener("scroll", update);
      window.removeEventListener("resize", update);
    };
  }, [activeSources.length]);

  const sourceCounts: Record<string, number> = {
    all: allItems.length,
    ...Object.fromEntries(activeSources.map((s) => [s, itemsBySource[s]?.length ?? 0])),
  };

  const filteredItems = active === "all" ? allItems : itemsBySource[active] ?? [];

  const yesterdayDate = (() => {
    const base = digest.daily.date ?? new Date().toISOString().slice(0, 10);
    const d = new Date(base);
    d.setDate(d.getDate() - 1);
    return d.toISOString().slice(0, 10);
  })();

  const sections =
    active === "all"
      ? activeSources
          .filter((s) => (sourceCounts[s] ?? 0) > 0)
          .map((key) => ({ key, items: itemsBySource[key] ?? [] }))
      : [{ key: active, items: filteredItems }];

  return (
    <div className="space-y-6 sm:space-y-10">
      {/* Hero */}
      <section className="text-center py-4 sm:py-8">
        <div className="inline-flex items-center gap-2 mb-5">
          <span className="inline-flex items-center gap-1.5 px-4 py-1.5 rounded-full bg-accent-lime/10 text-accent-lime text-xs font-semibold border border-accent-lime/20">
            <TrendingUp className="h-3.5 w-3.5" />
            {t("today.updatedAt")}
          </span>
        </div>

        <h1 className="text-3xl sm:text-4xl md:text-5xl lg:text-6xl font-bold tracking-tight text-text-primary">
          ⚡ {t("today.title")}
        </h1>

        <p className="mt-4 text-sm sm:text-base md:text-lg text-text-secondary max-w-2xl mx-auto leading-relaxed">
          <span className="inline-flex items-center gap-2">
            <Calendar className="h-4 w-4" />
            {digest.daily.date}
            <span className="text-text-dim">·</span>
            {allItems.length} {t("today.items")}
            <span className="text-text-dim">·</span>
            <RelativeTime
              date={digest.generated_at}
              locale={locale}
              fallback={new Date(digest.generated_at).toLocaleString(
                locale === "zh" ? "zh-CN" : "en-US",
                { month: "short", day: "numeric", hour: "2-digit", minute: "2-digit" }
              )}
            />
          </span>
        </p>

        <div className="mt-5 flex items-center justify-center gap-2">
          <Link
            href={`/history/${yesterdayDate}/`}
            className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-surface-hover text-text-secondary hover:text-text-primary hover:bg-surface-elevated transition-colors text-xs font-medium"
          >
            <History className="h-3.5 w-3.5" />
            {t("today.yesterday")}
          </Link>
          <Link
            href="/history/"
            className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-surface-hover text-text-secondary hover:text-text-primary hover:bg-surface-elevated transition-colors text-xs font-medium"
          >
            {t("today.allHistory")}
          </Link>
        </div>
      </section>

      {/* Source tabs — sticky on scroll */}
      <nav className="sticky top-14 z-30 -mx-3 px-3 py-2 bg-surface/80 backdrop-blur-xl border-b border-surface-border/50 sm:relative sm:top-auto sm:mx-0 sm:px-0 sm:py-0 sm:bg-transparent sm:backdrop-blur-none sm:border-0">
        <div className="flex items-center gap-2 min-w-0">
          <div className="relative flex-1 min-w-0">
            {scrollState.left && (
              <div className="absolute left-0 top-0 bottom-1 w-6 bg-gradient-to-r from-surface-base to-transparent z-10 pointer-events-none" />
            )}
            {scrollState.right && (
              <div className="absolute right-0 top-0 bottom-1 w-6 bg-gradient-to-l from-surface-base to-transparent z-10 pointer-events-none" />
            )}
            <div
              ref={tabsRef}
              className="flex gap-1.5 overflow-x-auto scrollbar-hide pb-1 -mb-1"
            >
            {["all", ...activeSources].map((src) => {
            const meta = getSourceMeta(src);
            const count = sourceCounts[src] ?? 0;
            const isActive = active === src;
            return (
              <button
                key={src}
                onClick={() => {
                  setActive(src);
                  trackEvent("source_tab_click", { source: src });
                }}
                className={`
                  flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-semibold
                  whitespace-nowrap transition-all duration-150 shrink-0
                  focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent-violet/40
                  ${isActive
                    ? `${meta.bg} ${meta.color} border border-current/20`
                    : "bg-surface-hover text-text-dim hover:text-text-secondary border border-transparent"
                  }
                `}
              >
                {meta.icon}
                <span>{t(meta.labelKey)}</span>
                <span className={`tabular-nums ${isActive ? "opacity-80" : "opacity-50"}`}>{count}</span>
              </button>
            );
          })}
            </div>
          </div>
          {readCount > 0 && (
            <span className="hidden sm:inline-flex items-center gap-1 px-2 py-1 rounded-lg text-[11px] font-medium text-text-dim bg-surface-hover tabular-nums shrink-0">
              {t("today.readProgress", { read: readCount, total: allItems.length })}
            </span>
          )}
          <button
            onClick={() => {
              markAllAsRead(allItems.map((i) => i.id));
              trackEvent("mark_all_read", { count: allItems.length });
            }}
            className="hidden sm:inline-flex items-center gap-1 px-2.5 py-1.5 rounded-lg text-xs font-medium text-text-dim hover:text-text-primary hover:bg-surface-hover transition-colors shrink-0"
            title={t("today.markAllRead")}
          >
            <CheckCheck className="h-3.5 w-3.5" />
            {t("today.markAllRead")}
          </button>
        </div>
      </nav>

      {/* Content sections */}
      {sections.map(({ key, items }) => {
        const meta = getSourceMeta(key);
        const isAllView = active === "all";
        return (
          <section key={key}>
            {isAllView && (
              <div className="flex items-center gap-3 mb-4">
                <div className={`flex items-center justify-center h-8 w-8 rounded-lg ${meta.bg}`}>
                  <span className={meta.color}>{meta.icon}</span>
                </div>
                <h2 className="text-base sm:text-lg font-bold text-text-primary">{t(meta.labelKey)}</h2>
                <span className="text-xs font-semibold text-text-dim bg-surface-hover px-2 py-0.5 rounded-md tabular-nums">
                  {items.length}
                </span>
              </div>
            )}
            <div className="space-y-2 sm:space-y-2.5">
              <FeedList items={items} showRank={!isAllView} linkToDetail />
            </div>
          </section>
        );
      })}

      {/* Subscribe */}
      <SubscribeForm />

      {/* Empty state */}
      {filteredItems.length === 0 && (
        <EmptyState title={t("today.empty")} />
      )}
    </div>
  );
}
