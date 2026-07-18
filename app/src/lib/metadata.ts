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
  ogImage?: string;
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
      images: [{ url: ogImage, width: 1200, height: 630, alt: title }],
    },
    twitter: {
      card: "summary_large_image",
      title,
      description,
      images: [ogImage],
    },
  };
}
