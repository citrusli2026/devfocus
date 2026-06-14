#!/usr/bin/env python3
from __future__ import annotations

"""Fetch Reddit r/programming hot posts."""

import json
import sys
import urllib.request
import urllib.error
from datetime import datetime, timezone
from pathlib import Path

REDDIT_URL = "https://www.reddit.com/r/programming/hot.json?limit=30"
HEADERS = {
    "User-Agent": "DevFocus/1.0 (https://devfocus.dev)",
    "Accept": "application/json",
}


def main():
    output_dir = Path(__file__).resolve().parent.parent / "2-raw"
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / "reddit_programming.json"

    print("[Reddit] Fetching r/programming hot posts...")
    req = urllib.request.Request(REDDIT_URL, headers=HEADERS)

    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            data = json.loads(resp.read().decode())
    except (urllib.error.URLError, TimeoutError, OSError) as e:
        print(f"[Reddit] Network error (skipping): {e}", file=sys.stderr)
        # Don't exit with error — Reddit may be blocked. Just skip.
        if output_path.exists():
            print("[Reddit] Using cached data from previous run")
        else:
            print("[Reddit] No cached data available, skipping")
        return

    posts = []
    for child in data.get("data", {}).get("children", []):
        d = child.get("data", {})
        if d.get("stickied"):
            continue
        posts.append({
            "id": d.get("id", ""),
            "title": d.get("title", ""),
            "url": d.get("url", ""),
            "score": d.get("score", 0),
            "num_comments": d.get("num_comments", 0),
            "author": d.get("author", ""),
            "created_utc": d.get("created_utc", 0),
            "permalink": f"https://reddit.com{d.get('permalink', '')}",
            "selftext": (d.get("selftext", "") or "")[:300],
            "source": "reddit",
        })

    posts.sort(key=lambda x: x["score"], reverse=True)

    result = {
        "fetched_at": datetime.now(timezone.utc).isoformat(),
        "source": "reddit",
        "count": len(posts),
        "items": posts,
    }
    output_path.write_text(json.dumps(result, indent=2, ensure_ascii=False))
    print(f"[Reddit] Saved {len(posts)} posts to {output_path}")


if __name__ == "__main__":
    main()
