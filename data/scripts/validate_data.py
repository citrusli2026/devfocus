#!/usr/bin/env python3
"""Validate final data files for consistency and completeness.

Run as part of CI after the pipeline finishes.
"""

import json
from datetime import datetime, timezone
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent.parent / "4-final"


def load(name: str) -> dict:
    path = DATA_DIR / name
    if not path.exists():
        raise FileNotFoundError(f"{path} not found")
    return json.loads(path.read_text(encoding="utf-8"))


def validate_feed(feed: dict) -> None:
    items = feed.get("items", [])
    assert isinstance(items, list), "feed.items must be a list"
    assert len(items) > 0, "feed.items must not be empty"

    ids = [i.get("id") for i in items]
    assert all(ids), "all items must have an id"
    assert len(ids) == len(set(ids)), "duplicate item ids found"

    required = {"title", "url", "description", "source", "time", "tags"}
    for item in items:
        missing = required - set(item.keys())
        assert not missing, f"item {item.get('id')} missing fields: {missing}"
        assert isinstance(item.get("tags", []), list), f"item {item['id']} tags must be a list"


def validate_digest(digest: dict) -> None:
    daily = digest.get("daily", {})
    items = daily.get("items", [])
    assert isinstance(items, list), "digest.daily.items must be a list"
    assert len(items) > 0, "digest.daily.items must not be empty"
    for item in items:
        assert item.get("id"), "digest item must have id"
        assert item.get("summary_zh") or item.get("summary_en"), \
            f"digest item {item.get('id')} must have a summary"


def validate_search_index(index: dict) -> None:
    items = index.get("items", [])
    assert isinstance(items, list), "search-index.items must be a list"
    assert len(items) > 0, "search-index.items must not be empty"

    required = {"id", "title", "url", "source", "domain", "score", "date", "tags", "hasDetail"}
    for item in items:
        missing = required - set(item.keys())
        assert not missing, f"search item {item.get('id')} missing fields: {missing}"

    # All dates must be parseable
    for item in items:
        datetime.strptime(item["date"], "%Y-%m-%d")


def validate_stats(stats: dict) -> None:
    assert "total_items" in stats, "stats must have total_items"
    assert "sources" in stats, "stats must have sources"
    assert "source_counts" in stats, "stats must have source_counts"
    assert isinstance(stats["source_counts"], dict), "stats.source_counts must be a dict"


def main() -> int:
    print("[Validate] feed.json")
    validate_feed(load("feed.json"))

    print("[Validate] digest.json")
    validate_digest(load("digest.json"))

    print("[Validate] search-index.json")
    validate_search_index(load("search-index.json"))

    print("[Validate] stats.json")
    validate_stats(load("stats.json"))

    print("[Validate] OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
