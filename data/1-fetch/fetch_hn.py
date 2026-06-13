#!/usr/bin/env python3
from __future__ import annotations

"""Hacker News Top Stories fetcher. Uses official Firebase API, no auth needed."""

import json
import sys
import urllib.request
import urllib.error
from datetime import datetime, timezone
from pathlib import Path

HN_TOP_URL = "https://hacker-news.firebaseio.com/v0/topstories.json"
HN_ITEM_URL = "https://hacker-news.firebaseio.com/v0/item/{}.json"
MAX_ITEMS = 50


def fetch_json(url: str, timeout: int = 15):
    """Fetch JSON from URL."""
    req = urllib.request.Request(url, headers={"User-Agent": "DevPulse/1.0"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode())


def fetch_item(item_id: int) -> dict | None:
    """Fetch a single HN item."""
    try:
        return fetch_json(HN_ITEM_URL.format(item_id))
    except (urllib.error.URLError, TimeoutError) as e:
        print(f"  [WARN] Failed to fetch item {item_id}: {e}", file=sys.stderr)
        return None


def main():
    output_dir = Path(__file__).resolve().parent.parent / "2-raw"
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / "hn_top_stories.json"

    print(f"[HN] Fetching top stories (max {MAX_ITEMS})...")
    try:
        top_ids = fetch_json(HN_TOP_URL)
    except Exception as e:
        print(f"[ERROR] Failed to fetch top stories: {e}", file=sys.stderr)
        sys.exit(1)

    top_ids = top_ids[:MAX_ITEMS]
    print(f"[HN] Got {len(top_ids)} story IDs, fetching details...")

    stories = []
    for i, sid in enumerate(top_ids):
        item = fetch_item(sid)
        if item and item.get("type") == "story":
            stories.append({
                "id": item["id"],
                "title": item.get("title", ""),
                "url": item.get("url", ""),
                "score": item.get("score", 0),
                "by": item.get("by", ""),
                "time": item.get("time", 0),
                "time_iso": datetime.fromtimestamp(item.get("time", 0), tz=timezone.utc).isoformat(),
                "descendants": item.get("descendants", 0),
                "hn_url": f"https://news.ycombinator.com/item?id={item['id']}",
                "source": "hackernews",
            })
        if (i + 1) % 10 == 0:
            print(f"  [{i+1}/{len(top_ids)}] fetched")

    # Sort by score descending
    stories.sort(key=lambda x: x["score"], reverse=True)

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
