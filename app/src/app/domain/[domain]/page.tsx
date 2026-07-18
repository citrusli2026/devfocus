import { notFound } from "next/navigation";
import digestData from "../../../data/digest.json";
import feedData from "../../../data/feed.json";
import { DomainClient, DomainItem } from "../../../components/DomainClient";
import type { Digest } from "../../../types";

type FeedItem = {
  id: string;
  title: string;
  url: string;
  description: string;
  source: string;
  time: string;
  domain?: string;
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

function normalizeDomain(domain: string): string {
  return domain.toLowerCase().replace(/^www\./, "");
}

function buildDomainMap(): Record<string, DomainItem[]> {
  const map: Record<string, DomainItem[]> = {};
  for (const item of feed.items) {
    const domain = normalizeDomain(item.domain || "");
    if (!domain) continue;
    if (!map[domain]) map[domain] = [];
    map[domain].push({
      id: item.id,
      title: item.title,
      url: item.url,
      description: item.description,
      source: item.source,
      date: extractDate(item.time),
      hasDetail: digestIds.has(item.id),
    });
  }
  // Sort each domain's items by date desc
  for (const key of Object.keys(map)) {
    map[key].sort((a, b) => b.date.localeCompare(a.date));
  }
  return map;
}

const domainMap = buildDomainMap();
// Only generate pages for domains with enough items
const MIN_DOMAIN_ITEMS = 3;
const domains = Object.keys(domainMap).filter((d) => (domainMap[d]?.length ?? 0) >= MIN_DOMAIN_ITEMS);

export async function generateStaticParams() {
  return domains.map((domain) => ({ domain }));
}

export default async function DomainPage({ params }: { params: Promise<{ domain: string }> }) {
  const { domain } = await params;
  const items = domainMap[normalizeDomain(domain)];
  if (!items || items.length === 0) return notFound();

  return <DomainClient domain={domain} items={items} />;
}
