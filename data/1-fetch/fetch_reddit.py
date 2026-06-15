#!/usr/bin/env python3
from __future__ import annotations

"""Fetch Reddit developer-relevant subreddits."""

import json
import sys
import time
import urllib.request
import urllib.error
from datetime import datetime, timezone
from pathlib import Path

SUBREDDITS = [
    "programming",
    "MachineLearning",
    "webdev",
    "rust",
    "golang",
    "devops",
]

HEADERS = {
    "User-Agent": "DevFocus/1.0 (https://devfocus.cc)",
    "Accept": "application/json",
}


def fetch_json(url: str, timeout: int = 15, retries: int = 3):
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, headers=HEADERS)
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                return json.loads(resp.read().decode())
        except (urllib.error.URLError, TimeoutError, OSError) as e:
            if attempt < retries - 1:
                time.sleep(2 ** attempt)
            else:
                raise


def main():
    output_dir = Path(__file__).resolve().parent.parent / "2-raw"
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / "reddit_programming.json"

    all_posts = []
    now = datetime.now(timezone.utc)

    for sub in SUBREDDITS:
        url = f"https://www.reddit.com/r/{sub}/hot.json?limit=20"
        print(f"[Reddit] Fetching r/{sub}...")
        try:
            data = fetch_json(url)
        except Exception as e:
            print(f"[Reddit] r/{sub} failed: {e}", file=sys.stderr)
            continue

        for child in data.get("data", {}).get("children", []):
            d = child.get("data", {})
            if d.get("stickied"):
                continue
            all_posts.append({
                "id": f"reddit-{d.get('id', '')}",
                "title": d.get("title", ""),
                "url": d.get("url", ""),
                "description": (d.get("selftext", "") or "")[:200],
                "source": "reddit",
                "score": d.get("score", 0),
                "comments": d.get("num_comments", 0),
                "author": d.get("author", ""),
                "time": datetime.fromtimestamp(d.get("created_utc", 0), tz=timezone.utc).isoformat(),
                "tags": [sub],
            })

        print(f"[Reddit] r/{sub}: {len(data.get('data', {}).get('children', []))} posts")
        time.sleep(1)  # Rate limit

    # Dedupe by title (cross-posts)
    seen = {}
    for post in all_posts:
        key = post["title"].lower().strip()
        if key not in seen or post["score"] > seen[key]["score"]:
            seen[key] = post
    all_posts = sorted(seen.values(), key=lambda x: x["score"], reverse=True)

    result = {
        "fetched_at": now.isoformat(),
        "source": "reddit",
        "count": len(all_posts),
        "items": all_posts,
    }
    output_path.write_text(json.dumps(result, indent=2, ensure_ascii=False))
    print(f"[Reddit] Total: {len(all_posts)} posts → {output_path.name}")


if __name__ == "__main__":
    main()
