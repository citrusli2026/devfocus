import { MetadataRoute } from "next";
import { SITE_URL } from "@/lib/metadata";

export const dynamic = "force-static";

export default function robots(): MetadataRoute.Robots {
  return {
    rules: {
      userAgent: "*",
      allow: "/",
      // trailingSlash 下搜索 URL 是 /search/?q=...，旧模式 "/search?*" 匹配不到
      disallow: "/search",
    },
    sitemap: `${SITE_URL}/sitemap.xml`,
    host: SITE_URL,
  };
}
