import { notFound } from "next/navigation";
import { promises as fs } from "fs";
import path from "path";
import { HistoryDateClient } from "../../../components/HistoryDateClient";
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

export async function generateStaticParams() {
  const files = await fs.readdir(HISTORY_DIR).catch(() => []);
  return files
    .filter((f) => f.endsWith(".json"))
    .map((f) => ({ date: f.replace(".json", "") }));
}

export default async function HistoryDatePage({ params }: { params: Promise<{ date: string }> }) {
  const { date } = await params;
  const history = await loadHistory(date);
  // Prefer curated digest_items (with summaries) when available; fall back to full snapshot.
  const items = history?.digest_items?.length ? history.digest_items : history?.items;
  if (!history || !items?.length) return notFound();

  return <HistoryDateClient date={history.date} items={items} />;
}
