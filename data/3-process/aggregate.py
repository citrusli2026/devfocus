#!/usr/bin/env python3
from __future__ import annotations

"""Aggregate all raw data sources into unified feed items."""

import json
from datetime import datetime, timezone, timedelta
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
RAW_DIR = BASE_DIR / "2-raw"
FINAL_DIR = BASE_DIR / "4-final"


def load_raw(filename: str) -> dict | None:
    """Load a raw JSON file, return None if missing."""
    path = RAW_DIR / filename
    if not path.exists():
        print(f"[AGG] {filename} not found, skipping")
        return None
    return json.loads(path.read_text())


def aggregate_hn(data: dict) -> list[dict]:
    """Convert HN stories to unified format."""
    items = []
    for s in data.get("items", []):
        items.append({
            "id": f"hn-{s['id']}",
            "title": s["title"],
            "url": s.get("url") or s.get("hn_url", ""),
            "description": "",
            "source": "hackernews",
            "score": s.get("score", 0),
            "comments": s.get("descendants", 0),
            "author": s.get("by", ""),
            "time": s.get("time_iso", ""),
            "tags": [],
        })
    return items


def aggregate_github(data: dict) -> list[dict]:
    """Convert GitHub trending to unified format."""
    items = []
    for r in data.get("items", []):
        items.append({
            "id": f"gh-{r['full_name'].replace('/', '-')}",
            "title": r["full_name"],
            "url": r.get("url", ""),
            "description": r.get("description", ""),
            "source": "github_trending",
            "score": r.get("stars_today", 0),
            "comments": 0,
            "author": r["full_name"].split("/")[0] if "/" in r["full_name"] else "",
            "time": data.get("fetched_at", ""),
            "tags": [],
        })
    return items


def compute_date_key(dt: datetime) -> str:
    """Get YYYY-MM-DD date key."""
    return dt.strftime("%Y-%m-%d")


def group_by_date(items: list[dict]) -> dict[str, list[dict]]:
    """Group items by date."""
    groups: dict[str, list[dict]] = {}
    for item in items:
        try:
            dt = datetime.fromisoformat(item["time"].replace("Z", "+00:00"))
            key = compute_date_key(dt)
        except (ValueError, KeyError):
            key = compute_date_key(datetime.now(timezone.utc))
        groups.setdefault(key, []).append(item)
    return groups


def main():
    FINAL_DIR.mkdir(parents=True, exist_ok=True)
    now = datetime.now(timezone.utc)

    all_items = []

    # Process HN
    hn_data = load_raw("hn_top_stories.json")
    if hn_data:
        all_items.extend(aggregate_hn(hn_data))
        print(f"[AGG] HN: {len(hn_data.get('items', []))} items")

    # Process GitHub
    gh_data = load_raw("gh_trending.json")
    if gh_data:
        all_items.extend(aggregate_github(gh_data))
        print(f"[AGG] GitHub: {len(gh_data.get('items', []))} items")

    # Sort all items by score descending
    all_items.sort(key=lambda x: x["score"], reverse=True)

    # Group by date
    by_date = group_by_date(all_items)

    # Build daily digest
    today_key = compute_date_key(now)
    today_items = by_date.get(today_key, all_items[:30])  # fallback to top items

    # Build weekly (last 7 days)
    week_ago = now - timedelta(days=7)
    weekly_items = [i for i in all_items if _parse_time(i) >= week_ago] or all_items[:100]

    # Final output
    digest = {
        "generated_at": now.isoformat(),
        "daily": {
            "date": today_key,
            "items": today_items[:30],
            "count": len(today_items[:30]),
        },
        "weekly": {
            "start": compute_date_key(week_ago),
            "end": today_key,
            "items": weekly_items[:100],
            "count": len(weekly_items[:100]),
        },
        "sources": list({i["source"] for i in all_items}),
        "total_items": len(all_items),
    }

    out_path = FINAL_DIR / "digest.json"
    out_path.write_text(json.dumps(digest, indent=2, ensure_ascii=False))
    print(f"[AGG] Saved digest to {out_path} ({len(all_items)} total items)")

    # Also save full feed for history
    feed_path = FINAL_DIR / "feed.json"
    feed = {
        "generated_at": now.isoformat(),
        "items": all_items,
        "by_date": {k: v for k, v in sorted(by_date.items(), reverse=True)},
    }
    feed_path.write_text(json.dumps(feed, indent=2, ensure_ascii=False))
    print(f"[AGG] Saved full feed to {feed_path}")


def _parse_time(item: dict) -> datetime:
    """Parse item time, fallback to epoch."""
    try:
        return datetime.fromisoformat(item["time"].replace("Z", "+00:00"))
    except (ValueError, KeyError):
        return datetime.min.replace(tzinfo=timezone.utc)


if __name__ == "__main__":
    main()
