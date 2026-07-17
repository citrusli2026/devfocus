"use client";

import Link from "next/link";
import { ArrowLeft, Calendar, ExternalLink, Trophy } from "lucide-react";
import { useTranslation } from "../lib/i18n";
import { getSourceMeta } from "../lib/sources";
import { EmptyState } from "./EmptyState";

export type PeriodItem = {
  id: string;
  title: string;
  url: string;
  description: string;
  source: string;
  date: string;
  score: number;
  hasDetail: boolean;
};

export function PeriodClient({
  period,
  items,
}: {
  period: "weekly" | "monthly";
  items: PeriodItem[];
}) {
  const { t } = useTranslation();

  const title = period === "weekly" ? t("period.weeklyTitle") : t("period.monthlyTitle");
  const subtitle = period === "weekly" ? t("period.weeklySubtitle") : t("period.monthlySubtitle");

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      <div className="flex items-center gap-3 text-sm text-text-muted">
        <Link
          href="/"
          className="inline-flex items-center gap-1.5 hover:text-text-primary transition-colors"
        >
          <ArrowLeft className="h-4 w-4" />
          {t("search.backToToday")}
        </Link>
      </div>

      <section className="text-center py-4">
        <div className="inline-flex items-center gap-2 mb-4">
          <span className="inline-flex items-center gap-1.5 px-4 py-1.5 rounded-full bg-accent-amber/10 text-accent-amber text-xs font-semibold border border-accent-amber/20">
            <Trophy className="h-3.5 w-3.5" />
            {t("period.badge")}
          </span>
        </div>
        <h1 className="text-3xl sm:text-4xl font-bold tracking-tight text-text-primary">
          {title}
        </h1>
        <p className="mt-2 text-text-secondary">{subtitle}</p>
      </section>

      <div className="space-y-3">
        {items.map((item, idx) => {
          const meta = getSourceMeta(item.source);
          const titleLink = item.hasDetail ? `/item/${item.id}/` : item.url;
          return (
            <article
              key={item.id}
              className="group p-4 rounded-xl bg-surface-card border border-surface-border hover:border-accent-violet/30 hover:shadow-sm transition-all"
            >
              <div className="flex items-start gap-3">
                <div className="flex items-center justify-center min-w-[2rem] h-8 rounded-lg bg-surface-hover text-text-dim text-sm font-bold tabular-nums">
                  {idx + 1}
                </div>
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
                    <span className="tabular-nums">🔥 {item.score.toLocaleString()}</span>
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

      {items.length === 0 && (
        <EmptyState title={t("period.emptyTitle")} hint={t("period.emptyHint")} icon="inbox" />
      )}
    </div>
  );
}
