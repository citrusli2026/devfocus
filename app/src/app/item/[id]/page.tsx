import { notFound } from "next/navigation";
import digestData from "../../../data/digest.json";
import feedData from "../../../data/feed.json";
import { ItemClient } from "../../../components/ItemClient";
import type { Digest, FeedItem } from "../../../types";

const digest = digestData as Digest;
const feed = feedData as unknown as { items: FeedItem[] };

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

export default async function ItemPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  const item = itemMap.get(id);
  if (!item || !hasDetailPage(item)) return notFound();

  const relatedItems = (item.related_ids ?? [])
    .map((rid) => itemMap.get(rid))
    .filter((i): i is NonNullable<typeof i> => Boolean(i))
    .slice(0, 5);

  return <ItemClient item={item} relatedItems={relatedItems} />;
}
