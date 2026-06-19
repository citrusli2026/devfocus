#!/usr/bin/env python3
from __future__ import annotations

"""Fetch Juejin (掘金) hot articles via API."""

import json
import sys
import time
import urllib.request
import urllib.error
from datetime import datetime, timezone
from pathlib import Path

API_URL = "https://api.juejin.cn/recommend_api/v1/article/recommend_all_feed"
TOP_N = 10


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
    print(f"[Juejin] Got {len(items)} articles")

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
