import type { Metadata } from "next";

export const SITE_URL = "https://www.devfocus.cc";
export const SITE_NAME = "DevFocus";
export const SITE_NAME_ZH = "DevFocus - 开发者聚焦";
export const DEFAULT_DESCRIPTION =
  "开发者关注的 AI 热榜、GitHub 趋势、技术新闻、36氪、知乎科技，每日自动整理的一站式技术资讯聚合站";
export const DEFAULT_OG_IMAGE = `${SITE_URL}/og.png`;

export function buildMetadata({
  title,
  description = DEFAULT_DESCRIPTION,
  path,
  ogImage = DEFAULT_OG_IMAGE,
  noIndex = false,
}: {
  title: string;
  description?: string;
  path: string;
  /** Pass null to omit explicit images so a route-level opengraph-image file is used. */
  ogImage?: string | null;
  noIndex?: boolean;
}): Metadata {
  const url = `${SITE_URL}${path}`;
  return {
    title,
    description,
    alternates: {
      canonical: url,
    },
    robots: noIndex ? { index: false, follow: false } : { index: true, follow: true },
    openGraph: {
      type: "website",
      locale: "zh_CN",
      alternateLocale: "en_US",
      siteName: SITE_NAME,
      title,
      description,
      url,
      ...(ogImage ? { images: [{ url: ogImage, width: 1200, height: 630, alt: title }] } : {}),
    },
    twitter: {
      card: "summary_large_image",
      title,
      description,
      // item 页 ogImage=null 走路由级 opengraph-image（OG 爬虫可用），
      // twitter:image 路由级文件不生成，回退到站点默认图避免卡片无图
      images: [ogImage ?? DEFAULT_OG_IMAGE],
    },
  };
}
