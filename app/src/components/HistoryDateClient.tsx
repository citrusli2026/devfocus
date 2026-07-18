"use client";

import Link from "next/link";
import { Calendar, ArrowLeft } from "lucide-react";
import { FeedList } from "./FeedCard";
import { getSourceMeta } from "../lib/sources";
import { useTranslation } from "../lib/i18n";
import type { FeedItem } from "../types";

export function HistoryDateClient({
  date,
  items,
  total,
}: {
  date: string;
  items: FeedItem[];
  total?: number;
}) {
  const { t } = useTranslation();

  const bySource: Record<string, FeedItem[]> = {};
  for (const item of items) {
    bySource[item.source] = bySource[item.source] ?? [];
    bySource[item.source].push(item);
  }
  const sources = Object.keys(bySource);

  return (
    <div className="space-y-8">
      <div className="flex items-center gap-3 text-sm text-text-muted">
        <Link
          href="/"
          className="inline-flex items-center gap-1.5 hover:text-text-primary transition-colors"
        >
          <ArrowLeft className="h-4 w-4" />
          {t("historyDate.backToToday")}
        </Link>
      </div>

      <section className="text-center py-4">
        <div className="inline-flex items-center gap-2 mb-4">
          <span className="inline-flex items-center gap-1.5 px-4 py-1.5 rounded-full bg-accent-violet/10 text-accent-violet text-xs font-semibold border border-accent-violet/20">
            <Calendar className="h-3.5 w-3.5" />
            {t("historyDate.badge")}
          </span>
        </div>
        <h1 className="text-3xl sm:text-4xl font-bold tracking-tight text-text-primary">
          {date}
        </h1>
        <p className="mt-2 text-text-secondary">
          {total && total > items.length
            ? t("historyDate.itemsCountCapped", { items: items.length, total, sources: sources.length })
            : t("historyDate.itemsCount", { items: items.length, sources: sources.length })}
        </p>
      </section>

      <div className="space-y-8">
        {sources.map((src) => {
          const meta = getSourceMeta(src);
          const srcItems = bySource[src];
          return (
            <section key={src}>
              <div className="flex items-center gap-3 mb-4">
                <div className={`flex items-center justify-center h-8 w-8 rounded-lg ${meta.bg}`}>
                  <span className={meta.color}>{meta.icon}</span>
                </div>
                <h2 className="text-base sm:text-lg font-bold text-text-primary">
                  {meta.shortLabel}
                </h2>
                <span className="text-xs font-semibold text-text-dim bg-surface-hover px-2 py-0.5 rounded-md tabular-nums">
                  {srcItems.length}
                </span>
              </div>
              <div className="space-y-2 sm:space-y-2.5">
                <FeedList items={srcItems} showRank={false} />
              </div>
            </section>
          );
        })}
      </div>

      <div className="flex justify-center pt-8 border-t border-surface-border">
        <Link
          href="/"
          className="inline-flex items-center gap-2 px-5 py-2.5 rounded-full bg-surface-hover text-text-secondary hover:text-text-primary hover:bg-surface-elevated transition-colors text-sm font-medium"
        >
          <ArrowLeft className="h-4 w-4" />
          {t("historyDate.backToTodayButton")}
        </Link>
      </div>
    </div>
  );
}
