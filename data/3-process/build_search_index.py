#!/usr/bin/env python3
"""Build a compact search index from feed.json + digest.json.

Output: 4-final/search-index.json
Includes recent/high-quality items with a flag for items that have detail pages.
"""

import json
from datetime import datetime, timezone
from pathlib import Path

DATA = Path(__file__).resolve().parent.parent
FEED_PATH = DATA / "4-final" / "feed.json"
DIGEST_PATH = DATA / "4-final" / "digest.json"
OUTPUT = DATA / "4-final" / "search-index.json"

DAYS_BACK = 30
MAX_ITEMS = 1000


def parse_time(t):
    try:
        return datetime.fromisoformat(str(t).replace("Z", "+00:00"))
    except (ValueError, TypeError):
        return None


def main():
    if not FEED_PATH.exists():
        print("[SearchIndex] feed.json not found, skipping")
        return

    feed = json.loads(FEED_PATH.read_text())
    items = feed.get("items", [])

    digest_ids = set()
    if DIGEST_PATH.exists():
        digest = json.loads(DIGEST_PATH.read_text())
        digest_ids = {i["id"] for i in digest.get("daily", {}).get("items", []) if i.get("id")}

    now = datetime.now(timezone.utc)
    cutoff = now.timestamp() - DAYS_BACK * 24 * 60 * 60

    scored = []
    for item in items:
        dt = parse_time(item.get("time"))
        if dt is None:
            continue
        ts = dt.timestamp()
        if ts < cutoff:
            continue
        scored.append((item.get("score", 0), ts, item))

    # Sort by score desc, then recency desc
    scored.sort(key=lambda x: (x[0], x[1]), reverse=True)
    selected = [x[2] for x in scored[:MAX_ITEMS]]

    # Stable sort by date desc for predictable display
    selected.sort(key=lambda x: parse_time(x.get("time")) or datetime.min.replace(tzinfo=timezone.utc), reverse=True)

    index_items = []
    for item in selected:
        dt = parse_time(item.get("time"))
        index_items.append({
            "id": item.get("id", ""),
            "title": item.get("title", ""),
            "url": item.get("url", ""),
            "description": item.get("description", ""),
            "source": item.get("source", ""),
            "score": item.get("score", 0),
            "comments": item.get("comments", 0),
            "date": dt.strftime("%Y-%m-%d") if dt else "",
            "tags": item.get("tags", []) or [],
            "hasDetail": item.get("id", "") in digest_ids,
        })

    result = {
        "generated_at": now.isoformat(),
        "total": len(index_items),
        "items": index_items,
    }

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(result, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    print(f"[SearchIndex] {len(index_items)} items → {OUTPUT}")


if __name__ == "__main__":
    main()
