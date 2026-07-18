import { notFound } from "next/navigation";
import digestData from "../../../data/digest.json";
import feedData from "../../../data/feed.json";
import { TagClient, TagItem } from "../../../components/TagClient";
import type { Digest } from "../../../types";

type FeedItem = {
  id: string;
  title: string;
  url: string;
  description: string;
  source: string;
  time: string;
  tags: string[];
};

type FeedData = {
  items: FeedItem[];
};

const digest = digestData as Digest;
const digestIds = new Set(digest.daily.items.map((i) => i.id));
const feed = feedData as unknown as FeedData;

function extractDate(time: string): string {
  try {
    return new Date(time).toISOString().slice(0, 10);
  } catch {
    return "";
  }
}

function normalizeTag(tag: string): string {
  return tag.toLowerCase().replace(/\s+/g, "-");
}

function buildTagMap(): Record<string, TagItem[]> {
  const map: Record<string, TagItem[]> = {};
  for (const item of feed.items) {
    if (!item.tags || item.tags.length === 0) continue;
    for (const tag of item.tags) {
      const key = normalizeTag(tag);
      if (!map[key]) map[key] = [];
      map[key].push({
        id: item.id,
        title: item.title,
        url: item.url,
        description: item.description,
        source: item.source,
        date: extractDate(item.time),
        hasDetail: digestIds.has(item.id),
      });
    }
  }
  // Sort each tag's items by date desc
  for (const key of Object.keys(map)) {
    map[key].sort((a, b) => b.date.localeCompare(a.date));
  }
  return map;
}

const tagMap = buildTagMap();
// Only generate pages for tags with enough items to avoid noise and keep build fast.
const MIN_TAG_ITEMS = 5;
const tags = Object.keys(tagMap).filter((tag) => (tagMap[tag]?.length ?? 0) >= MIN_TAG_ITEMS);

export async function generateStaticParams() {
  return tags.map((tag) => ({ tag }));
}

export default async function TagPage({ params }: { params: Promise<{ tag: string }> }) {
  const { tag } = await params;
  const items = tagMap[normalizeTag(tag)];
  if (!items || items.length === 0) return notFound();

  return <TagClient tag={tag} items={items} />;
}
