import { notFound } from "next/navigation";
import Link from "next/link";
import { promises as fs } from "fs";
import path from "path";
import { Calendar, ArrowLeft } from "lucide-react";
import { FeedList } from "../../../components/FeedCard";
import { getSourceMeta } from "../../../lib/sources";
import type { FeedItem } from "../../../types";

const HISTORY_DIR = path.resolve(process.cwd(), "..", "data", "5-history");

interface HistoryData {
  date: string;
  fetched_at: string;
  items: FeedItem[];
}

async function loadHistory(date: string): Promise<HistoryData | null> {
  try {
    const text = await fs.readFile(path.join(HISTORY_DIR, `${date}.json`), "utf-8");
    return JSON.parse(text) as HistoryData;
  } catch {
    return null;
  }
}

export async function generateStaticParams() {
  const files = await fs.readdir(HISTORY_DIR).catch(() => []);
  return files
    .filter((f) => f.endsWith(".json"))
    .map((f) => ({ date: f.replace(".json", "") }));
}

export default async function HistoryPage({ params }: { params: Promise<{ date: string }> }) {
  const { date } = await params;
  const history = await loadHistory(date);
  if (!history || !history.items?.length) return notFound();

  const items = history.items;
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
          返回今日
        </Link>
      </div>

      <section className="text-center py-4">
        <div className="inline-flex items-center gap-2 mb-4">
          <span className="inline-flex items-center gap-1.5 px-4 py-1.5 rounded-full bg-accent-violet/10 text-accent-violet text-xs font-semibold border border-accent-violet/20">
            <Calendar className="h-3.5 w-3.5" />
            历史归档
          </span>
        </div>
        <h1 className="text-3xl sm:text-4xl font-bold tracking-tight text-text-primary">
          {history.date}
        </h1>
        <p className="mt-2 text-text-secondary">
          共 {items.length} 条内容 · {sources.length} 个来源
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
          回到今日精选
        </Link>
      </div>
    </div>
  );
}
