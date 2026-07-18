import { notFound } from "next/navigation";
import type { Metadata } from "next";
import { promises as fs } from "fs";
import path from "path";
import { HistoryDateClient } from "../../../components/HistoryDateClient";
import { buildMetadata } from "../../../lib/metadata";
import type { FeedItem } from "../../../types";

const HISTORY_DIR = path.resolve(process.cwd(), "..", "data", "5-history");

interface HistoryData {
  date: string;
  fetched_at: string;
  items: FeedItem[];
  digest_items?: FeedItem[];
}

async function loadHistory(date: string): Promise<HistoryData | null> {
  try {
    const text = await fs.readFile(path.join(HISTORY_DIR, `${date}.json`), "utf-8");
    return JSON.parse(text) as HistoryData;
  } catch {
    return null;
  }
}

export async function generateMetadata({ params }: { params: Promise<{ date: string }> }): Promise<Metadata> {
  const { date } = await params;
  const history = await loadHistory(date);
  const items = history?.digest_items?.length ? history.digest_items : history?.items;
  if (!history || !items?.length) {
    return buildMetadata({
      title: `归档 - ${date}`,
      description: `${date} 技术资讯归档页面`,
      path: `/history/${date}/`,
      noIndex: true,
    });
  }
  const headline = items[0];
  const description = `DevFocus ${date} 归档共 ${history.items.length} 条技术资讯${headline ? `，精选：${headline.title}` : ""}`;
  return buildMetadata({
    title: `${date} 技术资讯归档 | DevFocus`,
    description,
    path: `/history/${date}/`,
  });
}

export async function generateStaticParams() {
  const files = await fs.readdir(HISTORY_DIR).catch(() => []);
  return files
    .filter((f) => f.endsWith(".json"))
    .map((f) => ({ date: f.replace(".json", "") }));
}

const HISTORY_PAGE_SIZE = 60;

export default async function HistoryDatePage({ params }: { params: Promise<{ date: string }> }) {
  const { date } = await params;
  const history = await loadHistory(date);
  // Prefer curated digest_items (with summaries) when available; fall back to full snapshot.
  let items = history?.digest_items?.length ? history.digest_items : history?.items;
  if (!history || !items?.length) return notFound();

  // Cap the statically rendered list to keep daily archive pages small. Full history
  // remains available in data/5-history/ for search and future enrichment.
  items = items
    .slice()
    .sort((a, b) => (b.quality_score ?? 0) - (a.quality_score ?? 0))
    .slice(0, HISTORY_PAGE_SIZE);

  return <HistoryDateClient date={history.date} items={items} total={history.items.length} />;
}
