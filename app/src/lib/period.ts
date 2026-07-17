import digestData from "../data/digest.json";
import feedData from "../data/feed.json";
import type { Digest } from "../types";

type FeedItem = {
  id: string;
  title: string;
  url: string;
  description: string;
  source: string;
  score: number;
  time: string;
};

type FeedData = {
  by_date: Record<string, FeedItem[]>;
};

const digest = digestData as Digest;
const digestIds = new Set(digest.daily.items.map((i) => i.id));
const feed = feedData as unknown as FeedData;

export function buildPeriodItems(days: number, topN: number) {
  const dates = Object.keys(feed.by_date).sort().reverse();
  const selectedDates = dates.slice(0, days);

  const scored: { item: FeedItem; date: string }[] = [];
  for (const date of selectedDates) {
    for (const item of feed.by_date[date] ?? []) {
      scored.push({ item, date });
    }
  }

  scored.sort((a, b) => b.item.score - a.item.score);

  return scored.slice(0, topN).map(({ item, date }) => ({
    id: item.id,
    title: item.title,
    url: item.url,
    description: item.description,
    source: item.source,
    date,
    score: item.score,
    hasDetail: digestIds.has(item.id),
  }));
}
