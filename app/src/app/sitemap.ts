import { MetadataRoute } from "next";
import { promises as fs } from "fs";
import path from "path";
import digestData from "@/data/digest.json";
import feedData from "@/data/feed.json";
import { SITE_URL } from "@/lib/metadata";
import type { Digest, FeedItem } from "@/types";

export const dynamic = "force-static";

const digest = digestData as Digest;
const feed = feedData as { items: FeedItem[] };

const HISTORY_DIR = path.resolve(process.cwd(), "..", "data", "5-history");

function safeDate(value?: string | null): Date | null {
  if (!value) return null;
  try {
    const d = new Date(value);
    if (Number.isNaN(d.getTime())) return null;
    return d;
  } catch {
    return null;
  }
}

function latestDate(items: FeedItem[]): Date | null {
  let latest: Date | null = null;
  for (const item of items) {
    const d = safeDate(item.time);
    if (d && (!latest || d > latest)) latest = d;
  }
  return latest;
}

function normalizeTag(tag: string): string {
  return tag.toLowerCase().replace(/\s+/g, "-");
}

function normalizeDomain(domain: string): string {
  return domain.toLowerCase().replace(/^www\./, "");
}

function hasDetailPage(item: FeedItem): boolean {
  return Boolean(item.summary_zh) || digest.daily.items.some((i) => i.id === item.id);
}

export default async function sitemap(): Promise<MetadataRoute.Sitemap> {
  const now = new Date();
  const baseLast = safeDate(digest.generated_at) ?? now;

  // Static routes
  const staticEntries: MetadataRoute.Sitemap = [
    { url: `${SITE_URL}/`, lastModified: baseLast, changeFrequency: "daily", priority: 1 },
    { url: `${SITE_URL}/history/`, lastModified: baseLast, changeFrequency: "daily", priority: 0.8 },
    { url: `${SITE_URL}/weekly/`, lastModified: baseLast, changeFrequency: "weekly", priority: 0.7 },
    { url: `${SITE_URL}/monthly/`, lastModified: baseLast, changeFrequency: "weekly", priority: 0.7 },
    { url: `${SITE_URL}/about/`, lastModified: baseLast, changeFrequency: "monthly", priority: 0.5 },
    { url: `${SITE_URL}/search/`, lastModified: baseLast, changeFrequency: "monthly", priority: 0.3 },
  ];

  // Item detail pages
  const itemMap = new Map<string, FeedItem>();
  for (const item of feed.items ?? []) {
    itemMap.set(item.id, item);
  }
  for (const item of digest.daily.items) {
    itemMap.set(item.id, item);
  }
  const itemEntries: MetadataRoute.Sitemap = [];
  for (const item of itemMap.values()) {
    if (!hasDetailPage(item)) continue;
    itemEntries.push({
      url: `${SITE_URL}/item/${encodeURIComponent(item.id)}/`,
      lastModified: safeDate(item.time) ?? baseLast,
      changeFrequency: "weekly",
      priority: 0.7,
    });
  }

  // Tag pages
  const tagMap: Record<string, FeedItem[]> = {};
  for (const item of feed.items) {
    if (!item.tags?.length) continue;
    for (const tag of item.tags) {
      const key = normalizeTag(tag);
      (tagMap[key] ??= []).push(item);
    }
  }
  const MIN_TAG_ITEMS = 8;
  const tagEntries: MetadataRoute.Sitemap = [];
  for (const [tag, items] of Object.entries(tagMap)) {
    if (items.length < MIN_TAG_ITEMS) continue;
    tagEntries.push({
      url: `${SITE_URL}/tag/${encodeURIComponent(tag)}/`,
      lastModified: latestDate(items) ?? baseLast,
      changeFrequency: "weekly",
      priority: 0.6,
    });
  }

  // Domain pages
  const domainMap: Record<string, FeedItem[]> = {};
  for (const item of feed.items) {
    const domain = normalizeDomain(item.domain || "");
    if (!domain) continue;
    (domainMap[domain] ??= []).push(item);
  }
  const MIN_DOMAIN_ITEMS = 3;
  const domainEntries: MetadataRoute.Sitemap = [];
  for (const [domain, items] of Object.entries(domainMap)) {
    if (items.length < MIN_DOMAIN_ITEMS) continue;
    domainEntries.push({
      url: `${SITE_URL}/domain/${encodeURIComponent(domain)}/`,
      lastModified: latestDate(items) ?? baseLast,
      changeFrequency: "weekly",
      priority: 0.6,
    });
  }

  // Daily history pages
  const files = await fs.readdir(HISTORY_DIR).catch(() => [] as string[]);
  const dates = files
    .filter((f) => f.endsWith(".json"))
    .map((f) => f.replace(".json", ""))
    .sort()
    .reverse();
  const historyEntries: MetadataRoute.Sitemap = dates.map((date) => ({
    url: `${SITE_URL}/history/${encodeURIComponent(date)}/`,
    lastModified: safeDate(date) ?? baseLast,
    changeFrequency: "daily",
    priority: 0.5,
  }));

  return [
    ...staticEntries,
    ...itemEntries,
    ...tagEntries,
    ...domainEntries,
    ...historyEntries,
  ];
}
