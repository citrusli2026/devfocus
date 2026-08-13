#!/usr/bin/env python3
from __future__ import annotations

"""Fetch Juejin (掘金) hot articles via API.

正文来源：推荐 API 只给 brief_content，完整正文从文章详情页 SSR 的
web_html_content 字段提取（无 cookie 可访问），失败条目 content 留空降级。
"""

import json
import re
import sys
import urllib.request
import urllib.error
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path

from _common import html_to_text

API_URL = "https://api.juejin.cn/recommend_api/v1/article/recommend_all_feed"
TOP_N = 20  # 多抓留出余量，下游 aggregate 取 Top 10
CONTENT_MAX_CHARS = 2000


def fetch_article_content(aid: str) -> str:
    """从文章详情页 SSR 提取正文（web_html_content 字段）。失败返回空串。"""
    url = f"https://juejin.cn/post/{aid}"
    try:
        req = urllib.request.Request(url, headers={
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)",
            "Accept": "text/html",
        })
        with urllib.request.urlopen(req, timeout=15) as resp:
            html = resp.read().decode("utf-8", errors="replace")
        # SSR 里的字段形如 web_html_content:"...\u003C..."（key 无引号，值带 JSON 转义）
        m = re.search(r'web_html_content:"((?:\\.|[^"\\])*)"', html)
        if not m:
            return ""
        body_html = json.loads(f'"{m.group(1)}"')
        return html_to_text(body_html, max_chars=CONTENT_MAX_CHARS)
    except Exception:
        return ""


def fetch_articles() -> list[dict]:
    """Fetch recommended articles from Juejin API."""
    body = json.dumps({
        "id_type": 2,
        "sort_type": 200,  # hot
        "cate_id": "",
        "cursor": "0",
        "limit": TOP_N,
    }).encode()

    req = urllib.request.Request(API_URL, data=body, headers={
        "Content-Type": "application/json",
        "User-Agent": "DevFocus/1.0 (https://devfocus.cc)",
    })

    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode())
            items = data.get("data", [])
            results = []
            for t in items:
                ai = t.get("item_info", {}).get("article_info", {})
                if not ai.get("title"):
                    continue
                aid = ai.get("article_id", "")
                results.append({
                    "id": f"juejin-{aid}",
                    "title": ai.get("title", ""),
                    "url": f"https://juejin.cn/post/{aid}",
                    "description": ai.get("brief_content", "")[:200],
                    "source": "juejin",
                    "score": ai.get("digg_count", 0),
                    "comments": ai.get("comment_count", 0),
                    "author": "",
                    "time": datetime.fromtimestamp(
                        int(ai.get("mtime", "0")), tz=timezone.utc
                    ).isoformat() if ai.get("mtime") else datetime.now(timezone.utc).isoformat(),
                    "tags": ["juejin"],
                })
            return results
    except Exception as e:
        print(f"[Juejin] API error: {e}", file=sys.stderr)
        return []


def main():
    output_dir = Path(__file__).resolve().parent.parent / "2-raw"
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / "juejin_daily.json"

    print("[Juejin] Fetching hot articles...")
    items = fetch_articles()
    if not items:
        # 抓取失败或 API 返回空：保留旧缓存（新鲜空文件会覆盖好数据，
        # 且新鲜时间戳会绕过 aggregate 的 STALE_HOURS 缺席检测导致源静默消失）
        if output_path.exists():
            old = json.loads(output_path.read_text())
            if old.get("items"):
                print(f"[Juejin] Fetch returned no items, keeping cached {len(old['items'])} items",
                      file=sys.stderr)
                return
        print("[Juejin] No items and no usable cache; writing empty result", file=sys.stderr)
    print(f"[Juejin] Got {len(items)} articles")

    # 并发抓正文（摘要阶段的输入素材）
    if items:
        with ThreadPoolExecutor(max_workers=8) as ex:
            contents = list(ex.map(lambda it: fetch_article_content(it["id"].replace("juejin-", "")), items))
        for it, c in zip(items, contents):
            it["content"] = c
        got = sum(1 for c in contents if c)
        print(f"[Juejin] content fetched: {got}/{len(items)}")

    result = {
        "fetched_at": datetime.now(timezone.utc).isoformat(),
        "source": "juejin",
        "count": len(items),
        "items": items,
    }
    output_path.write_text(json.dumps(result, indent=2, ensure_ascii=False))
    print(f"[Juejin] Saved to {output_path.name}")


if __name__ == "__main__":
    main()
