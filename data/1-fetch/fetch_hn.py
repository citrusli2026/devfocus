#!/usr/bin/env python3
from __future__ import annotations

"""Hacker News Top Stories fetcher with retry.

正文素材：帖子自述 text 直接收；外链帖对高分故事（top CONTENT_TOP_N）抓链接页面
正文（优先 meta description，其次页面全文），失败条目 content 留空降级。
"""

import json
import re
import sys
import time
import urllib.request
import urllib.error
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path

from _common import html_to_text

HN_TOP_URL = "https://hacker-news.firebaseio.com/v0/topstories.json"
HN_ITEM_URL = "https://hacker-news.firebaseio.com/v0/item/{}.json"
MAX_FETCH = 200
CONTENT_TOP_N = 30   # 外链正文只对 top N（按 score）抓，控制请求量
CONTENT_MAX_CHARS = 2000


def fetch_json(url: str, timeout: int = 15, retries: int = 3):
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "DevFocus/1.0"})
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                return json.loads(resp.read().decode())
        except (urllib.error.URLError, TimeoutError, OSError) as e:
            if attempt < retries - 1:
                wait = 2 ** attempt
                print(f"  [RETRY {attempt+1}/{retries}] {e}, waiting {wait}s...")
                time.sleep(wait)
            else:
                raise


def fetch_link_content(url: str) -> str:
    """抓外链页面正文：优先 meta description，其次页面全文。失败返回空串。"""
    if not url or not url.startswith("http"):
        return ""
    try:
        req = urllib.request.Request(url, headers={
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)",
            "Accept": "text/html",
        })
        with urllib.request.urlopen(req, timeout=12) as resp:
            html = resp.read(300_000).decode("utf-8", errors="replace")
        # 反爬验证页特征（Cloudflare 等）→ 视为无正文
        if "Checking your browser" in html or "JavaScript is disabled" in html \
                or "Enable JavaScript" in html or "cf-challenge" in html:
            return ""
        m = re.search(r'<meta[^>]+name=["\']description["\'][^>]+content=["\']([^"\']*)["\']', html, re.I)
        if m:
            return html_to_text(m.group(1), max_chars=CONTENT_MAX_CHARS)
        return html_to_text(html, max_chars=CONTENT_MAX_CHARS)
    except Exception:
        return ""


def main():
    output_dir = Path(__file__).resolve().parent.parent / "2-raw"
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / "hn_top_stories.json"

    print(f"[HN] Fetching top stories (max {MAX_FETCH})...")
    try:
        top_ids = fetch_json(HN_TOP_URL)
    except Exception as e:
        print(f"[ERROR] Failed to fetch top stories after retries: {e}", file=sys.stderr)
        # Use cached data if available
        if output_path.exists():
            print("[HN] Using cached data from previous run")
            return
        sys.exit(1)

    top_ids = top_ids[:MAX_FETCH]
    print(f"[HN] Got {len(top_ids)} IDs, fetching details...")

    stories = []
    for i, sid in enumerate(top_ids):
        try:
            item = fetch_json(HN_ITEM_URL.format(sid), retries=2)
        except Exception:
            continue
        if item and item.get("type") == "story":
            stories.append({
                "id": item["id"],
                "title": item.get("title", ""),
                "url": item.get("url", ""),
                "text": item.get("text", ""),  # 自述帖正文（HTML），外链帖为空
                "score": item.get("score", 0),
                "by": item.get("by", ""),
                "time": item.get("time", 0),
                "time_iso": datetime.fromtimestamp(item.get("time", 0), tz=timezone.utc).isoformat(),
                "descendants": item.get("descendants", 0),
                "hn_url": f"https://news.ycombinator.com/item?id={item['id']}",
                "source": "hackernews",
            })
        if (i + 1) % 20 == 0:
            print(f"  [{i+1}/{len(top_ids)}] fetched")

    stories.sort(key=lambda x: x["score"], reverse=True)

    # 正文素材：自述 text 全部取；外链帖只对 top N 抓链接正文（并发）
    for s in stories:
        s["content"] = html_to_text(s.pop("text", ""), max_chars=CONTENT_MAX_CHARS)
    link_stories = [s for s in stories[:CONTENT_TOP_N] if not s["content"]]
    if link_stories:
        with ThreadPoolExecutor(max_workers=8) as ex:
            contents = list(ex.map(lambda s: fetch_link_content(s["url"]), link_stories))
        for s, c in zip(link_stories, contents):
            s["content"] = c
        got = sum(1 for c in contents if c)
        print(f"[HN] link content fetched: {got}/{len(link_stories)}")
    else:
        print("[HN] all stories have self-post text or no link")

    result = {
        "fetched_at": datetime.now(timezone.utc).isoformat(),
        "source": "hackernews",
        "count": len(stories),
        "items": stories,
    }
    output_path.write_text(json.dumps(result, indent=2, ensure_ascii=False))
    print(f"[HN] Saved {len(stories)} stories to {output_path}")


if __name__ == "__main__":
    main()
