import type { Metadata } from "next";
import AboutClient from "@/components/AboutClient";
import { buildMetadata } from "@/lib/metadata";

export const metadata: Metadata = buildMetadata({
  title: "关于 DevFocus",
  description: "DevFocus 的项目介绍、数据来源、技术栈与统计信息。每日自动整理的开发者资讯聚合站。",
  path: "/about/",
});

export default function AboutPage() {
  return <AboutClient />;
}
