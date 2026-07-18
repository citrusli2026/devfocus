import type { Metadata } from "next";
import SearchPageClient from "@/components/SearchPageClient";
import { buildMetadata } from "@/lib/metadata";

export const metadata: Metadata = buildMetadata({
  title: "搜索 | DevFocus",
  description: "在 DevFocus 搜索技术资讯、文章、标签与历史归档。",
  path: "/search/",
});

export default function SearchPage() {
  return <SearchPageClient />;
}
