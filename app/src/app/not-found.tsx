import type { Metadata } from "next";
import NotFoundClient from "@/components/NotFoundClient";
import { buildMetadata } from "@/lib/metadata";

export const metadata: Metadata = buildMetadata({
  title: "页面未找到 | DevFocus",
  description: "你访问的页面不存在，返回首页或浏览历史归档。",
  path: "/",
  noIndex: true,
});

export default function NotFoundPage() {
  return <NotFoundClient />;
}
