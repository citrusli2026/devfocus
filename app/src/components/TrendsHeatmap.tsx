"use client";

import { useState } from "react";
import { useTranslation } from "../lib/i18n";
import * as rawTrendsData from "../data/trends.json";

type Topic = {
  keyword: string;
  count: number;
  total_heat: number;
  trend: string;
  heat_by_date: Record<string, number>;
  sample_titles?: string[];
};

const data = rawTrendsData as unknown as {
  generated_at: string;
  period: string;
  dates: string[];
  topics: Topic[];
  source_activity: Record<string, Record<string, number>>;
};

function heatOpacity(value: number, max: number): number {
  if (value === 0) return 0;
  const ratio = value / max;
  if (ratio > 0.75) return 1;
  if (ratio > 0.5) return 0.7;
  if (ratio > 0.25) return 0.45;
  return 0.2;
}

function Sparkline({ values, max }: { values: number[]; max: number }) {
  const w = 56;
  const h = 18;
  const padding = 2;
  const points = values.map((v, i) => {
    const x = padding + (i / (values.length - 1)) * (w - padding * 2);
    const y = h - padding - (v / max) * (h - padding * 2);
    return `${x},${y}`;
  });
  const path = `M ${points.join(" L ")}`;
  const areaPath = `${path} L ${w - padding},${h - padding} L ${padding},${h - padding} Z`;

  return (
    <svg width={w} height={h} className="flex-shrink-0">
      <defs>
        <linearGradient id="sparkGrad" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stopColor="rgb(139, 92, 246)" stopOpacity="0.3" />
          <stop offset="100%" stopColor="rgb(139, 92, 246)" stopOpacity="0" />
        </linearGradient>
      </defs>
      <path d={areaPath} fill="url(#sparkGrad)" />
      <path d={path} fill="none" stroke="rgb(139, 92, 246)" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
}

const TREND_BADGE: Record<string, { icon: string; color: string }> = {
  rising: { icon: "↑", color: "text-emerald-500 bg-emerald-500/10" },
  falling: { icon: "↓", color: "text-red-500 bg-red-500/10" },
  stable: { icon: "→", color: "text-gray-400 bg-gray-400/10" },
  new: { icon: "★", color: "text-amber-500 bg-amber-500/10" },
};

export function TrendsHeatmap() {
  const { t } = useTranslation();
  const [showAll, setShowAll] = useState(false);
  const [hoveredCell, setHoveredCell] = useState<{ topic: string; date: string; value: number } | null>(null);
  const [hoveredTopic, setHoveredTopic] = useState<string | null>(null);

  if (!data.topics || data.topics.length === 0) return null;

  const dates = data.dates;
  const topics = showAll ? data.topics : data.topics.slice(0, 10);

  const maxHeat = Math.max(
    ...data.topics.flatMap((tp: Topic) => Object.values(tp.heat_by_date))
  );

  const shortDate = (d: string) => {
    const parts = d.split("-");
    return `${parts[1]}/${parts[2]}`;
  };

  return (
    <div className="rounded-xl border border-surface-border bg-surface-elevated p-3 sm:p-5">
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-sm font-semibold text-text-primary flex items-center gap-1.5">
          🔥 {t("trends.title")}
        </h2>
        <span className="text-[10px] sm:text-xs text-text-muted font-mono">{data.period}</span>
      </div>

      {/* ===== Desktop: horizontal grid ===== */}
      <div className="hidden sm:block">
        {/* Date labels */}
        <div className="flex items-center gap-1 mb-3 pl-[160px]">
          {dates.map((d) => (
            <div key={d} className="flex-1 text-center text-[10px] text-text-muted font-mono">
              {shortDate(d)}
            </div>
          ))}
        </div>

        {/* Rows */}
        <div className="space-y-1.5">
          {topics.map((topic) => {
            const values = dates.map((d) => topic.heat_by_date[d] || 0);
            const topicMax = Math.max(...values, 1);
            const badge = TREND_BADGE[topic.trend] || TREND_BADGE.stable;

            return (
              <div key={topic.keyword} className="flex items-center gap-2 group">
                {/* Label */}
                <div
                  className="w-[150px] flex-shrink-0 relative cursor-default"
                  onMouseEnter={() => setHoveredTopic(topic.keyword)}
                  onMouseLeave={() => setHoveredTopic(null)}
                >
                  <div className="flex items-center gap-1.5">
                    <span className="text-xs font-medium text-text-primary truncate">
                      {topic.keyword}
                    </span>
                    <span className={`text-[9px] px-1 py-0.5 rounded-full font-medium ${badge.color}`}>
                      {badge.icon}
                    </span>
                  </div>
                  {hoveredTopic === topic.keyword && topic.sample_titles && topic.sample_titles.length > 0 && (
                    <div className="absolute left-0 bottom-full mb-2 w-[280px] px-3 py-2 bg-gray-900 text-white text-[11px] rounded-lg z-20 shadow-xl pointer-events-none">
                      <div className="font-medium text-violet-300 mb-1.5 text-xs">{topic.keyword}</div>
                      {topic.sample_titles.slice(0, 2).map((title, i) => (
                        <div key={i} className="text-gray-300 leading-relaxed truncate">· {title}</div>
                      ))}
                      <div className="absolute left-4 top-full w-0 h-0 border-l-4 border-r-4 border-t-4 border-transparent border-t-gray-900" />
                    </div>
                  )}
                </div>

                {/* Cells */}
                <div className="flex-1 flex items-center gap-1">
                  {dates.map((d) => {
                    const val = topic.heat_by_date[d] || 0;
                    const opacity = heatOpacity(val, maxHeat);
                    return (
                      <div
                        key={d}
                        className="flex-1 aspect-square rounded-[3px] transition-all duration-150 cursor-pointer hover:ring-1 hover:ring-violet-400/50 hover:scale-110 relative"
                        style={{ backgroundColor: `rgba(139, 92, 246, ${opacity})` }}
                        onMouseEnter={() => setHoveredCell({ topic: topic.keyword, date: d, value: val })}
                        onMouseLeave={() => setHoveredCell(null)}
                      >
                        {hoveredCell?.topic === topic.keyword && hoveredCell?.date === d && (
                          <div className="absolute bottom-full left-1/2 -translate-x-1/2 mb-2 px-2 py-1 bg-gray-900 text-white text-[10px] rounded-md whitespace-nowrap z-10 shadow-lg pointer-events-none">
                            <span className="font-medium">{topic.keyword}</span>
                            <span className="mx-1 text-gray-400">·</span>
                            <span className="font-mono">{shortDate(d)}</span>
                            <span className="mx-1 text-gray-400">·</span>
                            <span className="font-mono text-violet-300">{Math.round(val)}</span>
                          </div>
                        )}
                      </div>
                    );
                  })}
                </div>

                {/* Sparkline */}
                <div className="w-[60px] flex-shrink-0">
                  <Sparkline values={values} max={topicMax} />
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* ===== Mobile: stacked cards ===== */}
      <div className="sm:hidden space-y-2">
        {topics.map((topic) => {
          const values = dates.map((d) => topic.heat_by_date[d] || 0);
          const topicMax = Math.max(...values, 1);
          const badge = TREND_BADGE[topic.trend] || TREND_BADGE.stable;
          const lastVal = values[values.length - 1];
          const prevVal = values[values.length - 2] || 0;
          const change = prevVal > 0 ? ((lastVal - prevVal) / prevVal * 100).toFixed(0) : null;

          return (
            <div key={topic.keyword} className="flex items-center gap-3 py-1.5">
              {/* Topic name + trend */}
              <div className="w-[90px] flex-shrink-0">
                <div className="flex items-center gap-1">
                  <span className="text-xs font-semibold text-text-primary truncate">{topic.keyword}</span>
                  <span className={`text-[9px] px-1 py-0.5 rounded-full font-medium ${badge.color}`}>
                    {badge.icon}
                  </span>
                </div>
                {change && (
                  <span className={`text-[10px] font-mono ${Number(change) >= 0 ? 'text-emerald-500' : 'text-red-500'}`}>
                    {Number(change) >= 0 ? '+' : ''}{change}%
                  </span>
                )}
              </div>

              {/* Heat bar — single horizontal bar showing trend */}
              <div className="flex-1 flex items-center gap-0.5">
                {values.map((val, i) => {
                  const opacity = heatOpacity(val, maxHeat);
                  return (
                    <div
                      key={dates[i]}
                      className="flex-1 h-5 rounded-[2px] relative"
                      style={{ backgroundColor: `rgba(139, 92, 246, ${opacity})` }}
                      onTouchStart={() => setHoveredCell({ topic: topic.keyword, date: dates[i], value: val })}
                      onTouchEnd={() => setTimeout(() => setHoveredCell(null), 1500)}
                    >
                      {hoveredCell?.topic === topic.keyword && hoveredCell?.date === dates[i] && (
                        <div className="absolute bottom-full left-1/2 -translate-x-1/2 mb-1 px-1.5 py-0.5 bg-gray-900 text-white text-[9px] rounded whitespace-nowrap z-10 pointer-events-none">
                          {shortDate(dates[i])} · {Math.round(val)}
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>

              {/* Sparkline mini */}
              <div className="w-[44px] flex-shrink-0">
                <Sparkline values={values} max={topicMax} />
              </div>
            </div>
          );
        })}
      </div>

      {/* Legend + expand */}
      <div className="flex items-center justify-between mt-4 pt-3 border-t border-surface-border">
        <div className="flex items-center gap-1.5 text-[10px] text-text-muted">
          <span>{t("trends.less")}</span>
          {[0.1, 0.3, 0.6, 1].map((opacity, i) => (
            <div key={i} className="w-2.5 h-2.5 rounded-[2px]" style={{ backgroundColor: `rgba(139, 92, 246, ${opacity})` }} />
          ))}
          <span>{t("trends.more")}</span>
        </div>

        {data.topics.length > 10 && (
          <button
            onClick={() => setShowAll(!showAll)}
            className="text-xs text-accent-violet hover:text-accent-violet/80 transition-colors font-medium"
          >
            {showAll ? t("trends.showLess") : t("trends.showAll")}
          </button>
        )}
      </div>
    </div>
  );
}
