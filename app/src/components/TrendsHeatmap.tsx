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
};

// Type the imported data
const data = rawTrendsData as unknown as {
  generated_at: string;
  period: string;
  dates: string[];
  topics: Topic[];
  source_activity: Record<string, Record<string, number>>;
};

const TREND_ICONS: Record<string, string> = {
  rising: "🔺",
  falling: "🔻",
  stable: "➡️",
  new: "🆕",
};

function heatColor(value: number, max: number): string {
  if (value === 0) return "bg-surface-hover";
  const ratio = value / max;
  if (ratio > 0.75) return "bg-accent-violet";
  if (ratio > 0.5) return "bg-accent-violet/70";
  if (ratio > 0.25) return "bg-accent-violet/40";
  return "bg-accent-violet/20";
}

function heatTextColor(value: number, max: number): string {
  if (value === 0) return "text-text-muted";
  const ratio = value / max;
  if (ratio > 0.5) return "text-white";
  return "text-text-secondary";
}

export function TrendsHeatmap() {
  const { t } = useTranslation();
  const [showAll, setShowAll] = useState(false);

  if (!data.topics || data.topics.length === 0) return null;

  const dates = data.dates;
  const topics = showAll ? data.topics : data.topics.slice(0, 12);

  // Find max heat for color scaling
  const maxHeat = Math.max(
    ...data.topics.flatMap((tp: Topic) => Object.values(tp.heat_by_date))
  );

  // Short date display (MM/DD)
  const shortDate = (d: string) => {
    const parts = d.split("-");
    return `${parts[1]}/${parts[2]}`;
  };

  return (
    <div className="rounded-xl border border-surface-border bg-surface-elevated p-4 sm:p-5">
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-sm font-semibold text-text-primary flex items-center gap-1.5">
          🔥 {t("trends.title")}
        </h2>
        <span className="text-xs text-text-muted">{data.period}</span>
      </div>

      {/* Heatmap — horizontal scroll on mobile */}
      <div className="overflow-x-auto -mx-2 px-2">
        <table className="w-full text-xs">
          <thead>
            <tr>
              <th className="text-left pr-3 py-1 font-medium text-text-muted whitespace-nowrap sticky left-0 bg-surface-elevated">
                {t("trends.topic")}
              </th>
              <th className="text-center px-1 py-1 font-medium text-text-muted whitespace-nowrap">
                {t("trends.trend")}
              </th>
              {dates.map((d) => (
                <th
                  key={d}
                  className="text-center px-1 py-1 font-medium text-text-muted whitespace-nowrap min-w-[2.5rem]"
                >
                  {shortDate(d)}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {topics.map((topic) => (
              <tr key={topic.keyword} className="group">
                <td className="pr-3 py-1 font-medium text-text-primary whitespace-nowrap sticky left-0 bg-surface-elevated group-hover:bg-surface-hover transition-colors">
                  {topic.keyword}
                </td>
                <td className="text-center px-1 py-1">
                  <span title={topic.trend}>
                    {TREND_ICONS[topic.trend] || "➡️"}
                  </span>
                </td>
                {dates.map((d) => {
                  const val = topic.heat_by_date[d] || 0;
                  return (
                    <td
                      key={d}
                      className={`text-center px-1 py-1 min-w-[2.5rem] ${heatColor(val, maxHeat)} ${heatTextColor(val, maxHeat)} rounded-sm font-mono transition-colors`}
                      title={`${topic.keyword}: ${val.toFixed(0)}`}
                    >
                      {val > 0 ? (val >= 100 ? Math.round(val) : val.toFixed(0)) : ""}
                    </td>
                  );
                })}
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Legend */}
      <div className="flex items-center gap-3 mt-3 text-xs text-text-muted">
        <span className="flex items-center gap-1">
          🔺 {t("trends.rising")}
        </span>
        <span className="flex items-center gap-1">
          🔻 {t("trends.falling")}
        </span>
        <span className="flex items-center gap-1">
          ➡️ {t("trends.stable")}
        </span>
        <span className="flex items-center gap-1">
          🆕 {t("trends.newTopic")}
        </span>
      </div>

      {/* Show more/less */}
      {data.topics.length > 12 && (
        <button
          onClick={() => setShowAll(!showAll)}
          className="mt-3 text-xs text-accent-violet hover:text-accent-violet/80 transition-colors"
        >
          {showAll ? t("trends.showLess") : t("trends.showAll")}
        </button>
      )}
    </div>
  );
}
