"""Fetch hot articles from InfoQ China (developer/engineering content)."""
from __future__ import annotations

import json
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path

from _common import fetch_with_retry, html_to_text

OUT = Path(__file__).parent.parent / "2-raw" / "infoq.json"
API = "https://www.infoq.cn/public/v1/my/recommond"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)",
    "Content-Type": "application/json",
    "Referer": "https://www.infoq.cn/",
}

PAGE_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)",
    "Accept": "text/html",
    "Referer": "https://www.infoq.cn/",
}
CONTENT_MAX_CHARS = 2000


def fetch_article_content(uuid: str) -> str:
    """抓取文章页正文（ProseMirror 容器，服务端渲染）。失败返回空串。"""
    url = f"https://www.infoq.cn/article/{uuid}"
    try:
        req = urllib.request.Request(url, headers=PAGE_HEADERS)
        with urllib.request.urlopen(req, timeout=15) as resp:
            html = resp.read().decode("utf-8", errors="replace")
        return html_to_text(html, max_chars=CONTENT_MAX_CHARS, target_class="ProseMirror")
    except Exception:
        return ""


def fetch():
    payload = json.dumps({"size": 20}).encode()
    _, body = fetch_with_retry(API, timeout=30, method="POST", data=payload, headers=HEADERS)
    data = json.loads(body.decode())
    
    items = []
    for item in (data.get("data", []) or [])[:20]:
        # publish_time 为毫秒时间戳，统一转 ISO（与其他源口径一致）
        raw_time = item.get("publish_time") or 0
        try:
            time_iso = (datetime.fromtimestamp(int(raw_time) / 1000, tz=timezone.utc).isoformat()
                        if raw_time else "")
        except (ValueError, TypeError, OSError, OverflowError):
            time_iso = ""
        items.append({
            "id": str(item.get("uuid", "")),
            "title": item.get("article_title", ""),
            "url": f"https://www.infoq.cn/article/{item.get('uuid', '')}",
            "source": "infoq",
            "score": item.get("views", 0),
            "time": time_iso,
            "tags": [],
        })

    # 并发抓正文（摘要阶段的输入素材，失败条目 content 留空降级）
    if items:
        with ThreadPoolExecutor(max_workers=4) as ex:
            contents = list(ex.map(lambda it: fetch_article_content(it["id"]), items))
        for it, c in zip(items, contents):
            it["content"] = c
        got = sum(1 for c in contents if c)
        print(f"[InfoQ] content fetched: {got}/{len(items)}")

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps({
        "fetched_at": datetime.now(timezone.utc).isoformat(),
        "source": "infoq",
        "count": len(items),
        "items": items,
    }, ensure_ascii=False, indent=2))
    print(f"[InfoQ] {len(items)} articles -> {OUT}")

if __name__ == "__main__":
    fetch()
