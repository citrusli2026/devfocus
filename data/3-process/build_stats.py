#!/usr/bin/env python3
"""Compute and write site statistics from feed.json, digest.json and summaries.json.

Output: 4-final/stats.json
Used by the About page to show live, data-driven metrics.
"""

from __future__ import annotations

import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse

DATA = Path(__file__).resolve().parent.parent
FEED_PATH = DATA / "4-final" / "feed.json"
DIGEST_PATH = DATA / "4-final" / "digest.json"
SUMMARIES_PATH = DATA / "4-final" / "summaries.json"
OUTPUT = DATA / "4-final" / "stats.json"


def parse_time(t: str | int | float) -> datetime | None:
    try:
        # Handle Unix timestamps (seconds or milliseconds)
        if isinstance(t, (int, float)) and t > 0:
            if t > 1e12:
                t = t / 1000
            return datetime.fromtimestamp(t, tz=timezone.utc)
        # Handle ISO strings
        s = str(t)
        if s.isdigit():
            n = int(s)
            if n > 1e12:
                n = n / 1000
            return datetime.fromtimestamp(n, tz=timezone.utc)
        dt = datetime.fromisoformat(s.replace("Z", "+00:00"))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt
    except (ValueError, TypeError):
        return None


def domain(url: str) -> str:
    try:
        host = urlparse(url).hostname or ""
        return host.replace("www.", "")
    except Exception:
        return ""


def main():
    feed = json.loads(FEED_PATH.read_text()) if FEED_PATH.exists() else {"items": []}
    digest = json.loads(DIGEST_PATH.read_text()) if DIGEST_PATH.exists() else {}
    summaries = json.loads(SUMMARIES_PATH.read_text()) if SUMMARIES_PATH.exists() else {}

    items = feed.get("items", [])
    now = datetime.now(timezone.utc)

    # Basic counts
    total_items = len(items)
    unique_ids = len({i["id"] for i in items})

    # Date range
    parsed_times = [t for t in (parse_time(i.get("time", "")) for i in items) if t]
    if parsed_times:
        first_date = min(parsed_times)
        last_date = max(parsed_times)
        days_covered = (last_date - first_date).days + 1
    else:
        first_date = last_date = None
        days_covered = 0

    # Sources
    source_counts = Counter(i.get("source", "unknown") for i in items)
    sources = sorted(source_counts.keys())

    # Summaries: items that have an entry in summaries.json with real content
    summary_ids = set(summaries.keys())
    items_with_summary = sum(
        1 for i in items
        if i["id"] in summary_ids
        and len(summaries[i["id"]].get("summary_zh", "")) >= 20
    )
    total_summaries = len(summaries)

    # Engagement
    items_with_comments = sum(1 for i in items if i.get("comments", 0) > 0)
    total_comments = sum(i.get("comments", 0) for i in items)

    # Domains
    domain_counts = Counter(domain(i.get("url", "")) for i in items if i.get("url"))

    # Daily digest size
    daily_count = digest.get("daily", {}).get("count", 0)

    # Recency
    latest_update = digest.get("generated_at", last_date.isoformat() if last_date else "")

    stats = {
        "generated_at": now.isoformat(),
        "total_items": total_items,
        "unique_items": unique_ids,
        "days_covered": days_covered,
        "first_date": first_date.strftime("%Y-%m-%d") if first_date else "",
        "last_date": last_date.strftime("%Y-%m-%d") if last_date else "",
        "sources": sources,
        "source_counts": dict(source_counts.most_common()),
        "daily_count": daily_count,
        "items_with_summary": items_with_summary,
        "total_summaries": total_summaries,
        "items_with_comments": items_with_comments,
        "total_comments": total_comments,
        "top_domains": dict(domain_counts.most_common(10)),
        "latest_update": latest_update,
    }

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(stats, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"[Stats] {total_items} items, {days_covered} days → {OUTPUT}")


if __name__ == "__main__":
    main()
