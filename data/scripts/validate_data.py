#!/usr/bin/env python3
"""Validate final data files for consistency and completeness.

Run as part of CI after the pipeline finishes.
"""

import json
import re
from datetime import datetime, timezone
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent.parent / "4-final"

# 日榜预期覆盖的数据源（缺源只 WARN，配合 digest.missing_sources 使用）
EXPECTED_SOURCES = {
    "hackernews", "github_trending", "producthunt", "juejin",
    "zhihu", "36kr", "infoq", "v2ex",
}
MIN_DAILY_SOURCES = 7
MIN_SEARCH_SOURCES = 5


def load(name: str) -> dict:
    path = DATA_DIR / name
    if not path.exists():
        raise FileNotFoundError(f"{path} not found")
    return json.loads(path.read_text(encoding="utf-8"))


def _valid_time(t) -> bool:
    """time 必须是 ISO 8601 字符串，或可解析的 int/float 时间戳（秒或毫秒）。"""
    if isinstance(t, (int, float)) and not isinstance(t, bool) and t > 0:
        return True
    if isinstance(t, str) and t:
        try:
            datetime.fromisoformat(t.replace("Z", "+00:00"))
            return True
        except ValueError:
            return False
    return False


def _check_items_time(items: list[dict], where: str) -> None:
    for item in items:
        assert _valid_time(item.get("time")), \
            f"{where} item {item.get('id')} has invalid time: {item.get('time')!r} (must be ISO string or int timestamp)"


def _normalize_title(title: str) -> str:
    return re.sub(r"\s+", " ", title.lower().strip())


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

    _check_items_time(items, "feed")


def validate_digest(digest: dict) -> None:
    daily = digest.get("daily", {})
    items = daily.get("items", [])
    assert isinstance(items, list), "digest.daily.items must be a list"
    assert len(items) > 0, "digest.daily.items must not be empty"
    for item in items:
        assert item.get("id"), "digest item must have id"
        assert item.get("summary_zh") or item.get("summary_en"), \
            f"digest item {item.get('id')} must have a summary"

    _check_items_time(items, "digest.daily")
    _check_items_time(digest.get("monthly", {}).get("items", []), "digest.monthly")

    # 日榜标题去重（normalize 后重复视为数据质量问题）
    seen_titles: dict[str, str] = {}
    for item in items:
        key = _normalize_title(item.get("title", ""))
        assert key not in seen_titles, \
            f"duplicate title in digest daily: {item.get('title')!r} (ids: {seen_titles[key]}, {item.get('id')})"
        seen_titles[key] = item.get("id", "")

    # 日榜 source 覆盖度：缺源 WARN（不 fail），并核对 missing_sources 标注
    covered = {i.get("source") for i in items}
    missing = EXPECTED_SOURCES - covered
    if missing:
        print(f"[WARN] digest daily covers {len(covered)}/{len(EXPECTED_SOURCES)} sources "
              f"(expect >= {MIN_DAILY_SOURCES}), missing: {', '.join(sorted(missing))}")
        declared = set(digest.get("missing_sources", []))
        undeclared = missing - declared
        if undeclared:
            print(f"[WARN] missing sources not declared in digest.missing_sources: "
                  f"{', '.join(sorted(undeclared))}")


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

    # 源覆盖度：至少 MIN_SEARCH_SOURCES 个源，防止某个 fetch 大面积挂掉后索引塌缩
    sources = {i.get("source") for i in items}
    assert len(sources) >= MIN_SEARCH_SOURCES, \
        f"search-index covers only {len(sources)} sources (< {MIN_SEARCH_SOURCES}): {sorted(sources)}"


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
