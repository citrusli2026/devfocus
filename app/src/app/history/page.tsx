import { promises as fs } from "fs";
import path from "path";
import type { Metadata } from "next";
import { HistoryIndexClient } from "../../components/HistoryIndexClient";
import { buildMetadata } from "../../lib/metadata";

const HISTORY_DIR = path.resolve(process.cwd(), "..", "data", "5-history");

export const metadata: Metadata = buildMetadata({
  title: "归档日历 | DevFocus",
  description: "按日期浏览 DevFocus 每日技术资讯归档，包含 AI 热榜、GitHub 趋势、技术新闻等历史精选。",
  path: "/history/",
});

export default async function HistoryIndexPage() {
  const files = await fs.readdir(HISTORY_DIR).catch(() => []);
  const dates = files
    .filter((f) => f.endsWith(".json"))
    .map((f) => f.replace(".json", ""))
    .sort()
    .reverse();

  return <HistoryIndexClient dates={dates} />;
}
