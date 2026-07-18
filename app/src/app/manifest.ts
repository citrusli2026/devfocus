import type { MetadataRoute } from "next";

export const dynamic = "force-static";

export default function manifest(): MetadataRoute.Manifest {
  return {
    name: "DevFocus - 开发者聚焦",
    short_name: "DevFocus",
    description: "开发者关注的 AI 热榜、GitHub 趋势、技术新闻，每日自动整理",
    start_url: "/",
    display: "standalone",
    background_color: "#f5f3fa",
    theme_color: "#6a5fc1",
    icons: [
      {
        src: "/icon.svg",
        sizes: "any",
        type: "image/svg+xml",
      },
    ],
  };
}
