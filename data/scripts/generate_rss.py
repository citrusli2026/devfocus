#!/usr/bin/env python3
"""Generate RSS feed from digest.json → app/public/feed.xml."""

import json
import os
import xml.sax.saxutils as saxutils
from datetime import datetime, timezone
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
FINAL_DIR = BASE_DIR / "4-final"
APP_PUBLIC_DIR = BASE_DIR.parent / "app" / "public"

SITE_URL = "https://www.devfocus.cc"
FEED_TITLE = "DevFocus - 开发者聚焦"
FEED_DESC = "每日自动整理的开发者资讯：AI 热榜、GitHub 趋势、技术新闻"


def rss_datetime(dt_str: str) -> str:
    """Convert any timestamp to RFC 2822."""
    try:
        dt = datetime.fromisoformat(dt_str.replace("Z", "+00:00"))
        return dt.strftime("%a, %d %b %Y %H:%M:%S +0000")
    except (ValueError, AttributeError):
        return datetime.now(timezone.utc).strftime("%a, %d %b %Y %H:%M:%S +0000")


def escape(s: str) -> str:
    return saxutils.escape(s)


def rfc3339(dt_str: str) -> str:
    """Normalize to YYYY-MM-DD for sitemap lastmod."""
    try:
        dt = datetime.fromisoformat(dt_str.replace("Z", "+00:00"))
        return dt.strftime("%Y-%m-%d")
    except (ValueError, AttributeError):
        return datetime.now(timezone.utc).strftime("%Y-%m-%d")


def generate():
    APP_PUBLIC_DIR.mkdir(parents=True, exist_ok=True)
    digest_path = FINAL_DIR / "digest.json"
    if not digest_path.exists():
        print("[FEED] No digest.json found, skipping")
        return

    digest = json.loads(digest_path.read_text())
    daily = digest.get("daily", {})
    items = daily.get("items", [])
    date_str = daily.get("date", "")
    gen_date = rfc3339(digest.get("generated_at", ""))
    pub_date = rss_datetime(digest.get("generated_at", ""))

    # ——— Sitemap ———
    sitemap_xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <url>
    <loc>{SITE_URL}/</loc>
    <lastmod>{gen_date}</lastmod>
    <changefreq>daily</changefreq>
    <priority>1.0</priority>
  </url>
  <url>
    <loc>{SITE_URL}/about/</loc>
    <changefreq>monthly</changefreq>
    <priority>0.3</priority>
  </url>
  <url>
    <loc>{SITE_URL}/feed.xml</loc>
    <changefreq>daily</changefreq>
    <priority>0.5</priority>
  </url>
</urlset>"""
    sitemap_path = APP_PUBLIC_DIR / "sitemap.xml"
    sitemap_path.write_text(sitemap_xml, encoding="utf-8")
    print(f"[FEED] Sitemap → {sitemap_path}")

    # ——— RSS (only if there are daily items) ———
    if not items:
        print("[FEED] No daily items, skipping RSS")
        return

    rss_items = []
    seen_urls: set[str] = set()
    for item in items:
        url = item.get("url", "").strip()
        if not url or url in seen_urls:
            continue
        seen_urls.add(url)

        title = escape(item.get("title", ""))
        url_esc = escape(url)
        source = escape(item.get("source", ""))
        desc = escape((item.get("summary_en") or item.get("description", "") or item.get("title", ""))[:500])
        item_date = rss_datetime(item.get("time", ""))
        guid = escape(f"{item.get('id', url)}-{date_str}")

        rss_items.append(f"""    <item>
      <title>[{source}] {title}</title>
      <link>{url_esc}</link>
      <guid isPermaLink="false">{guid}</guid>
      <pubDate>{item_date}</pubDate>
      <description>{desc}</description>
      <source url="{SITE_URL}">DevFocus</source>
    </item>""")

    if not rss_items:
        print("[FEED] No items with valid URLs, skipping RSS")
        return

    rss_xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom">
  <channel>
    <title>{escape(FEED_TITLE)}</title>
    <link>{SITE_URL}</link>
    <description>{escape(FEED_DESC)}</description>
    <language>zh-cn</language>
    <lastBuildDate>{pub_date}</lastBuildDate>
    <pubDate>{pub_date}</pubDate>
    <ttl>60</ttl>
    <atom:link href="{SITE_URL}/feed.xml" rel="self" type="application/rss+xml"/>
    <image>
      <url>{SITE_URL}/favicon.ico</url>
      <title>{escape(FEED_TITLE)}</title>
      <link>{SITE_URL}</link>
    </image>
{chr(10).join(rss_items)}
  </channel>
</rss>"""

    out_path = APP_PUBLIC_DIR / "feed.xml"
    out_path.write_text(rss_xml, encoding="utf-8")
    print(f"[FEED] RSS {len(rss_items)} items → {out_path}")


if __name__ == "__main__":
    generate()
