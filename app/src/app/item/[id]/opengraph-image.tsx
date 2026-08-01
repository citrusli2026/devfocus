import { ImageResponse } from "next/og";
import digestData from "../../../data/digest.json";
import feedData from "../../../data/feed.json";
import { getSourceMeta } from "../../../lib/sources";
import type { Digest, FeedItem } from "../../../types";

export const alt = "DevFocus - 开发者聚焦";
export const size = { width: 1200, height: 630 };
export const contentType = "image/png";
export const dynamic = "force-static";

const digest = digestData as Digest;
const feed = feedData as unknown as { items: FeedItem[] };

// Same selection as the item detail page: daily digest entries override feed
// entries because they carry the generated summaries.
const itemMap = new Map<string, FeedItem>();
for (const item of feed.items ?? []) {
  itemMap.set(item.id, item);
}
for (const item of digest.daily.items) {
  itemMap.set(item.id, item);
}

function hasDetailPage(item: FeedItem): boolean {
  return Boolean(item.summary_zh) || digest.daily.items.some((i) => i.id === item.id);
}

export async function generateStaticParams() {
  return Array.from(itemMap.values())
    .filter(hasDetailPage)
    .map((item) => ({ id: item.id }));
}

export default async function Image({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  const item = itemMap.get(id);
  const title = item?.title ?? "DevFocus";
  const sourceLabel = item ? getSourceMeta(item.source).shortLabel : "";

  return new ImageResponse(
    (
      <div
        style={{
          width: "100%",
          height: "100%",
          display: "flex",
          flexDirection: "column",
          justifyContent: "center",
          padding: 80,
          background: "#f5f3fa",
          color: "#1a1530",
        }}
      >
        <div style={{ display: "flex", fontSize: 32, fontWeight: 700, marginBottom: 32 }}>
          <span>Dev</span>
          <span style={{ color: "#6a5fc1" }}>Focus</span>
        </div>
        <div
          style={{
            display: "flex",
            fontSize: 56,
            fontWeight: 700,
            lineHeight: 1.25,
            overflow: "hidden",
            textOverflow: "ellipsis",
          }}
        >
          {title}
        </div>
        <div style={{ display: "flex", marginTop: 40, fontSize: 28, color: "#6a5fc1" }}>
          {sourceLabel}
        </div>
      </div>
    ),
    { ...size }
  );
}
