"use client";

import { useState } from "react";
import Link from "next/link";
import { ArrowLeft, Flame, TrendingUp, TrendingDown, Minus, Sparkles } from "lucide-react";
import { useTranslation } from "../lib/i18n";
import { cn } from "../lib/utils";
import type { TrendsData, TrendTopic } from "../types";

const TOPIC_LIMIT = 20;

// 4 heat levels on the violet scale; index 0 = no data
const HEAT_CELL = [
  "bg-surface-hover/40",
  "bg-accent-violet/15",
  "bg-accent-violet/35",
  "bg-accent-violet/60",
  "bg-accent-violet/85",
];

function heatLevel(heat: number | undefined, max: number): number {
  if (!heat || max <= 0) return 0;
  const ratio = heat / max;
  if (ratio >= 0.75) return 4;
  if (ratio >= 0.5) return 3;
  if (ratio >= 0.25) return 2;
  return 1;
}

function TrendMark({ trend }: { trend: TrendTopic["trend"] }) {
  const { t } = useTranslation();
  const cfg = {
    rising: { icon: TrendingUp, cls: "text-accent-coral", label: t("trends.rising") },
    falling: { icon: TrendingDown, cls: "text-accent-cyan", label: t("trends.falling") },
    stable: { icon: Minus, cls: "text-text-dim", label: t("trends.stable") },
    new: { icon: Sparkles, cls: "text-accent-emerald", label: t("trends.new") },
  }[trend];
  const Icon = cfg.icon;
  return (
    <span title={cfg.label} aria-label={cfg.label} className="inline-flex shrink-0">
      <Icon className={cn("h-3.5 w-3.5", cfg.cls)} />
    </span>
  );
}

function HeatmapTable({ dates, topics }: { dates: string[]; topics: TrendTopic[] }) {
  const { t } = useTranslation();
  const [expanded, setExpanded] = useState<string | null>(null);

  return (
    <div className="bg-surface-card border border-surface-border rounded-xl overflow-hidden">
      <div className="overflow-x-auto">
        <table className="border-collapse text-xs">
          <thead>
            <tr className="border-b border-surface-border">
              <th className="sticky left-0 z-10 bg-surface-card text-left font-semibold text-text-muted px-3 py-2 min-w-36">
                {t("trends.topic")}
              </th>
              {dates.map((d) => (
                <th key={d} className="font-medium text-text-dim px-1 py-2 tabular-nums whitespace-nowrap">
                  {d.slice(5)}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {topics.map((topic) => {
              const max = Math.max(0, ...dates.map((d) => topic.heat_by_date[d] ?? 0));
              const isOpen = expanded === topic.keyword;
              return [
                <tr
                  key={topic.keyword}
                  onClick={() => setExpanded(isOpen ? null : topic.keyword)}
                  className={cn(
                    "cursor-pointer border-b border-surface-border/50 last:border-b-0",
                    isOpen && "bg-surface-hover/30"
                  )}
                >
                  <th className="sticky left-0 z-10 bg-surface-card text-left font-medium text-text-secondary px-3 py-1.5">
                    <span className="flex items-center gap-1.5">
                      <TrendMark trend={topic.trend} />
                      <span className="truncate max-w-28 sm:max-w-none">{topic.keyword}</span>
                      <span className="text-text-dim font-normal tabular-nums">{topic.count}</span>
                    </span>
                  </th>
                  {dates.map((d) => {
                    const heat = topic.heat_by_date[d];
                    const level = heatLevel(heat, max);
                    return (
                      <td key={d} className="p-0.5">
                        <div
                          className={cn("h-6 w-7 rounded-sm", HEAT_CELL[level])}
                          title={heat ? `${d} · ${heat}` : `${d} · 0`}
                        />
                      </td>
                    );
                  })}
                </tr>,
                isOpen && topic.sample_titles.length > 0 ? (
                  <tr key={`${topic.keyword}-samples`} className="border-b border-surface-border/50 last:border-b-0">
                    <td colSpan={dates.length + 1} className="sticky left-0 px-3 py-2.5 bg-surface-hover/30">
                      <div className="text-[11px] font-semibold text-text-dim uppercase tracking-wide mb-1.5">
                        {t("trends.samples")}
                      </div>
                      <ul className="space-y-1">
                        {topic.sample_titles.map((title, i) => (
                          <li key={i} className="flex items-start gap-2 text-text-secondary leading-relaxed">
                            <span className="mt-1.5 w-1 h-1 rounded-full bg-accent-violet/60 shrink-0" />
                            <span>{title}</span>
                          </li>
                        ))}
                      </ul>
                    </td>
                  </tr>
                ) : null,
              ];
            })}
          </tbody>
        </table>
      </div>
      {/* Legend */}
      <div className="flex items-center gap-4 px-3 py-2.5 border-t border-surface-border flex-wrap">
        <span className="flex items-center gap-1 text-[11px] text-text-dim">
          {t("trends.legendLow")}
          {[1, 2, 3, 4].map((l) => (
            <span key={l} className={cn("inline-block h-3 w-4 rounded-sm", HEAT_CELL[l])} />
          ))}
          {t("trends.legendHigh")}
        </span>
        {(["rising", "falling", "stable", "new"] as const).map((trend) => (
          <span key={trend} className="flex items-center gap-1 text-[11px] text-text-dim">
            <TrendMark trend={trend} />
            {t(`trends.${trend}`)}
          </span>
        ))}
      </div>
    </div>
  );
}

function SourceActivity({ dates, activity }: { dates: string[]; activity: TrendsData["source_activity"] }) {
  const { t } = useTranslation();
  const sources = Object.keys(activity);
  if (sources.length === 0) return null;

  return (
    <div className="bg-surface-card border border-surface-border rounded-xl p-4 sm:p-5">
      <h2 className="text-sm font-semibold text-text-muted mb-4 uppercase tracking-wide">
        {t("trends.sourceActivity")}
      </h2>
      <div className="space-y-2.5">
        {sources.map((source) => {
          const counts = activity[source];
          const max = Math.max(1, ...dates.map((d) => counts[d] ?? 0));
          return (
            <div key={source} className="flex items-center gap-3">
              <span className="w-24 sm:w-28 shrink-0 text-xs text-text-secondary truncate">{source}</span>
              <div className="flex-1 flex items-end gap-px h-6">
                {dates.map((d) => {
                  const count = counts[d] ?? 0;
                  return (
                    <div
                      key={d}
                      className="flex-1 rounded-sm bg-accent-violet/70"
                      style={{ height: count ? `${Math.max(12, (count / max) * 100)}%` : "2px", opacity: count ? 1 : 0.25 }}
                      title={`${source} · ${d} · ${count}`}
                    />
                  );
                })}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}

export function TrendsClient({ trends }: { trends: TrendsData }) {
  const { t } = useTranslation();
  const dates = trends.dates ?? [];
  const topics = (trends.topics ?? []).slice(0, TOPIC_LIMIT);

  return (
    <div className="space-y-8 max-w-5xl mx-auto">
      <div className="flex items-center gap-3 text-sm text-text-muted">
        <Link href="/" className="inline-flex items-center gap-1.5 hover:text-text-primary transition-colors">
          <ArrowLeft className="h-4 w-4" />
          {t("history.backToToday")}
        </Link>
      </div>

      <section className="text-center py-4">
        <div className="inline-flex items-center gap-2 mb-4">
          <span className="inline-flex items-center gap-1.5 px-4 py-1.5 rounded-full bg-accent-violet/10 text-accent-violet text-xs font-semibold border border-accent-violet/20">
            <Flame className="h-3.5 w-3.5" />
            {t("trends.badge")}
          </span>
        </div>
        <h1 className="text-3xl sm:text-4xl font-bold tracking-tight text-text-primary">
          {t("trends.title")}
        </h1>
        <p className="mt-2 text-text-secondary">{t("trends.subtitle", { period: trends.period })}</p>
      </section>

      {topics.length === 0 ? (
        <p className="text-center text-text-dim py-12">{t("trends.empty")}</p>
      ) : (
        <>
          <HeatmapTable dates={dates} topics={topics} />
          <SourceActivity dates={dates} activity={trends.source_activity ?? {}} />
        </>
      )}
    </div>
  );
}
