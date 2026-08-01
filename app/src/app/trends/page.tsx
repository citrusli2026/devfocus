import type { Metadata } from "next";
import trendsData from "../../data/trends.json";
import { TrendsClient } from "../../components/TrendsClient";
import { buildMetadata } from "../../lib/metadata";
import type { TrendsData } from "../../types";

const trends = trendsData as unknown as TrendsData;

export const metadata: Metadata = buildMetadata({
  title: "话题趋势 | DevFocus",
  description: "DevFocus 开发者话题趋势热力图：哪些技术话题在升温、哪些在降温，逐日热度一目了然。",
  path: "/trends/",
});

export default function TrendsPage() {
  return <TrendsClient trends={trends} />;
}
