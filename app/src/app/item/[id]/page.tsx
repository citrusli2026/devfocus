import { notFound } from "next/navigation";
import type { Metadata } from "next";
import { promises as fs } from "fs";
import path from "path";
import digestData from "../../../data/digest.json";
import feedData from "../../../data/feed.json";
import { ItemClient } from "../../../components/ItemClient";
import { buildMetadata } from "../../../lib/metadata";
import type { Digest, FeedItem, HeatPoint } from "../../../types";

const digest = digestData as Digest;
const feed = feedData as unknown as { items: FeedItem[] };

// Same repo-level snapshot directory used by app/history/[date]/page.tsx. It is
// read at build time only; if the directory is missing, pages just render
// without the heat sparkline.
const HISTORY_DIR = path.resolve(process.cwd(), "..", "data", "5-history");
const HEAT_WINDOW = 7;

interface HistorySnapshot {
  date: string;
  items: FeedItem[];
}

// Daily score history for an item over the most recent HEAT_WINDOW snapshots.
// feed.json's by_date buckets only cover curated subsets, so full history
// snapshots are the reliable source for multi-day presence. Matches by id,
// falling back to exact title match.
async function buildHeatHistory(id: string, title: string): Promise<HeatPoint[]> {
  let files: string[] = [];
  try {
    files = (await fs.readdir(HISTORY_DIR)).filter((f) => f.endsWith(".json")).sort().slice(-HEAT_WINDOW);
  } catch {
    return [];
  }
  const snapshots: HistorySnapshot[] = [];
  for (const file of files) {
    try {
      snapshots.push(JSON.parse(await fs.readFile(path.join(HISTORY_DIR, file), "utf-8")) as HistorySnapshot);
    } catch {}
  }
  const collect = (match: (i: FeedItem) => boolean): HeatPoint[] =>
    snapshots.flatMap((snap) => {
      const hit = (snap.items ?? []).find(match);
      return hit ? [{ date: snap.date, score: hit.score }] : [];
    });
  const byId = collect((i) => i.id === id);
  return byId.length > 0 ? byId : collect((i) => i.title === title);
}

// Build a map of all items that have ever appeared in the feed. Daily digest
// entries override feed entries because they carry the generated summaries.
const itemMap = new Map<string, FeedItem>();
for (const item of feed.items ?? []) {
  itemMap.set(item.id, item);
}
for (const item of digest.daily.items) {
  itemMap.set(item.id, item);
}

function hasDetailPage(item: FeedItem): boolean {
  // Only render full detail pages for items with a Chinese summary (real enrichment)
  // or items currently featured in the daily digest. This avoids generating thousands
  // of low-value item pages and keeps the static build small.
  return Boolean(item.summary_zh) || digest.daily.items.some((i) => i.id === item.id);
}

export async function generateStaticParams() {
  return Array.from(itemMap.values())
    .filter(hasDetailPage)
    .map((item) => ({ id: item.id }));
}

export async function generateMetadata({ params }: { params: Promise<{ id: string }> }): Promise<Metadata> {
  const { id } = await params;
  const item = itemMap.get(id);
  if (!item || !hasDetailPage(item)) {
    return buildMetadata({ title: "Not Found", path: "/", noIndex: true });
  }
  const summary = item.summary_zh || item.summary_en || item.description;
  return buildMetadata({
    title: item.title,
    description: summary.slice(0, 160),
    path: `/item/${id}/`,
    // ogImage omitted: use this route's generated opengraph-image
    ogImage: null,
  });
}

export default async function ItemPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  const item = itemMap.get(id);
  if (!item || !hasDetailPage(item)) return notFound();

  // Keep only related items that actually have a detail page, otherwise the
  // links rendered by ItemClient would 404.
  const relatedItems = (item.related_ids ?? [])
    .map((rid) => itemMap.get(rid))
    .filter((i): i is NonNullable<typeof i> => Boolean(i))
    .filter(hasDetailPage)
    .slice(0, 5);

  return <ItemClient item={item} relatedItems={relatedItems} heatHistory={await buildHeatHistory(item.id, item.title)} />;
}
