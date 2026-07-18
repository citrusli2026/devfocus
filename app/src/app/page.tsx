import type { Metadata } from "next";
import HomeClient from "@/components/HomeClient";
import { buildMetadata } from "@/lib/metadata";

export const metadata: Metadata = buildMetadata({
  title: "DevFocus - 开发者聚焦",
  description: "开发者关注的 AI 热榜、GitHub 趋势、技术新闻、36氪、知乎科技，每日自动整理的一站式技术资讯聚合站。",
  path: "/",
});

export default function HomePage() {
  return <HomeClient />;
}
