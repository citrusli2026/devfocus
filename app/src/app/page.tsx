"use client";

import { useState } from "react";
import { Digest } from "../types";
import { FeedList } from "../components/FeedCard";
import { useTranslation } from "../lib/i18n";
import { TrendingUp } from "lucide-react";
import { GitHubIcon } from "../components/icons";
import digestData from "../data/digest.json";

type SourceKey = "all" | "hackernews" | "github_trending" | "producthunt" | "juejin" | "zhihu";

const SOURCE_META: Record<SourceKey, { labelKey: string; icon: React.ReactNode; color: string; bg: string }> = {
  all:        { labelKey: "today.allSources",  icon: null,                         color: "text-accent-violet", bg: "bg-accent-violet/10" },
  hackernews: { labelKey: "today.hnTitle",      icon: <span className="text-sm">🔥</span>, color: "text-[#ff6600]",    bg: "bg-[#ff6600]/10" },
  github_trending: { labelKey: "today.ghTitle", icon: <GitHubIcon className="h-4 w-4" />,   color: "text-accent-emerald", bg: "bg-accent-emerald/10" },
  producthunt:{ labelKey: "today.phTitle",      icon: <span className="text-sm">🚀</span>, color: "text-[#da552f]",    bg: "bg-[#da552f]/10" },
  juejin:     { labelKey: "today.juejinTitle",  icon: <span className="text-sm">📘</span>, color: "text-[#1e80ff]",    bg: "bg-[#1e80ff]/10" },
  zhihu:      { labelKey: "today.zhihuTitle",   icon: <span className="text-sm">💬</span>, color: "text-[#0066ff]",    bg: "bg-[#0066ff]/10" },
};

export default function Home() {
  const { t } = useTranslation();
  const digest = digestData as Digest;
  const [active, setActive] = useState<SourceKey>("all");

  const allItems = digest.daily.items;
  const bySource = (src: string) => allItems.filter((i) => i.source === src);

  const hnItems = bySource("hackernews");
  const ghItems = bySource("github_trending");
  const phItems = bySource("producthunt");
  const jjItems = bySource("juejin");
  const zhItems = bySource("zhihu");

  // Build source counts for tabs
  const sourceCounts: Partial<Record<SourceKey, number>> = {
    all: allItems.length,
    hackernews: hnItems.length,
    github_trending: ghItems.length,
    producthunt: phItems.length,
    juejin: jjItems.length,
    zhihu: zhItems.length,
  };

  const activeSources: SourceKey[] = (["hackernews", "github_trending", "producthunt", "juejin", "zhihu"] as SourceKey[])
    .filter((s) => (sourceCounts[s] ?? 0) > 0);

  // Filtered items for active tab
  const filteredItems = active === "all" ? allItems : allItems.filter((i) => i.source === active);

  // Group items by source for "all" view
  const sections: { key: SourceKey; items: typeof allItems }[] = active === "all"
    ? [
        hnItems.length > 0 && { key: "hackernews" as SourceKey, items: hnItems },
        ghItems.length > 0 && { key: "github_trending" as SourceKey, items: ghItems },
        phItems.length > 0 && { key: "producthunt" as SourceKey, items: phItems },
        jjItems.length > 0 && { key: "juejin" as SourceKey, items: jjItems },
        zhItems.length > 0 && { key: "zhihu" as SourceKey, items: zhItems },
      ].filter(Boolean) as { key: SourceKey; items: typeof allItems }[]
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
          {digest.daily.date} · {allItems.length} {t("today.items")}
        </p>
      </section>

      {/* Source tabs — sticky on scroll */}
      <nav className="sticky top-14 z-30 -mx-3 px-3 py-2 bg-surface/80 backdrop-blur-xl border-b border-surface-border/50 sm:relative sm:top-auto sm:mx-0 sm:px-0 sm:py-0 sm:bg-transparent sm:backdrop-blur-none sm:border-0">
        <div className="flex gap-1.5 overflow-x-auto scrollbar-hide pb-1 -mb-1">
          {(["all", ...activeSources] as SourceKey[]).map((src) => {
            const meta = SOURCE_META[src];
            const count = sourceCounts[src] ?? 0;
            const isActive = active === src;
            return (
              <button
                key={src}
                onClick={() => setActive(src)}
                className={`
                  flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-semibold
                  whitespace-nowrap transition-all duration-150 shrink-0
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
      </nav>

      {/* Content sections */}
      {sections.map(({ key, items }) => {
        const meta = SOURCE_META[key];
        // All-view: show source header + 2-col grid on desktop
        // Single-source view: clean list, no header
        if (active === "all") {
          return (
            <section key={key}>
              <div className="flex items-center gap-3 mb-4">
                <div className={`flex items-center justify-center h-8 w-8 rounded-lg ${meta.bg}`}>
                  <span className={meta.color}>{meta.icon}</span>
                </div>
                <h2 className="text-base sm:text-lg font-bold text-text-primary">{t(meta.labelKey)}</h2>
                <span className="text-xs font-semibold text-text-dim bg-surface-hover px-2 py-0.5 rounded-md tabular-nums">
                  {items.length}
                </span>
              </div>
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
                <FeedList items={items.slice(0, Math.ceil(items.length / 2))} />
                <FeedList items={items.slice(Math.ceil(items.length / 2))} rankOffset={Math.ceil(items.length / 2)} />
              </div>
            </section>
          );
        }

        // Single source view — clean list
        return (
          <section key={key}>
            <FeedList items={items} />
          </section>
        );
      })}

      {/* Empty state */}
      {filteredItems.length === 0 && (
        <div className="text-center py-12 text-text-muted">
          <p className="text-lg">{t("today.empty")}</p>
        </div>
      )}
    </div>
  );
}
