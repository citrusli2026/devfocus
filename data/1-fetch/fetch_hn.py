#!/usr/bin/env python3
from __future__ import annotations

"""Hacker News Top Stories fetcher with retry."""

import json
import sys
import time
import urllib.request
import urllib.error
from datetime import datetime, timezone
from pathlib import Path

HN_TOP_URL = "https://hacker-news.firebaseio.com/v0/topstories.json"
HN_ITEM_URL = "https://hacker-news.firebaseio.com/v0/item/{}.json"
MAX_FETCH = 200


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
