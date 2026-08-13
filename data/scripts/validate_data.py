#!/usr/bin/env python3
"""Validate final data files for consistency and completeness.

Run as part of CI after the pipeline finishes.

注意：不用 assert（python -O 下会被剥离导致校验静默失效），
统一用 check() 抛出 ValidationError；所有文件都校验完后一次性汇总输出。
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

TREND_VALUES = {"rising", "falling", "stable", "new"}


class ValidationError(Exception):
    pass


def check(cond, msg: str) -> None:
    if not cond:
        raise ValidationError(msg)


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
        check(_valid_time(item.get("time")),
              f"{where} item {item.get('id')} has invalid time: {item.get('time')!r}"
              " (must be ISO string or int timestamp)")


def _normalize_title(title: str) -> str:
    return re.sub(r"\s+", " ", title.lower().strip())


def validate_feed(feed: dict) -> None:
    items = feed.get("items", [])
    check(isinstance(items, list), "feed.items must be a list")
    check(len(items) > 0, "feed.items must not be empty")

    ids = [i.get("id") for i in items]
    check(all(ids), "all items must have an id")
    check(len(ids) == len(set(ids)), "duplicate item ids found")

    required = {"title", "url", "description", "source", "time", "tags"}
    for item in items:
        missing = required - set(item.keys())
        check(not missing, f"item {item.get('id')} missing fields: {missing}")
        check(isinstance(item.get("tags", []), list), f"item {item['id']} tags must be a list")

    _check_items_time(items, "feed")


def validate_digest(digest: dict) -> None:
    daily = digest.get("daily", {})
    items = daily.get("items", [])
    check(isinstance(items, list), "digest.daily.items must be a list")
    check(len(items) > 0, "digest.daily.items must not be empty")
    for item in items:
        check(item.get("id"), "digest item must have id")
        check(item.get("summary_zh") or item.get("summary_en"),
              f"digest item {item.get('id')} must have a summary")

    _check_items_time(items, "digest.daily")
    _check_items_time(digest.get("monthly", {}).get("items", []), "digest.monthly")

    # 日榜标题去重（normalize 后重复视为数据质量问题）
    # 注意：check() 的参数会立即求值，不能像 assert 那样惰性构造消息
    seen_titles: dict[str, str] = {}
    for item in items:
        key = _normalize_title(item.get("title", ""))
        if key in seen_titles:
            check(False,
                  f"duplicate title in digest daily: {item.get('title')!r}"
                  f" (ids: {seen_titles[key]}, {item.get('id')})")
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
    check(isinstance(items, list), "search-index.items must be a list")
    check(len(items) > 0, "search-index.items must not be empty")

    required = {"id", "title", "url", "source", "domain", "score", "date", "tags", "hasDetail"}
    for item in items:
        missing = required - set(item.keys())
        check(not missing, f"search item {item.get('id')} missing fields: {missing}")

    # All dates must be parseable
    for item in items:
        datetime.strptime(item["date"], "%Y-%m-%d")

    # 源覆盖度：至少 MIN_SEARCH_SOURCES 个源，防止某个 fetch 大面积挂掉后索引塌缩
    sources = {i.get("source") for i in items}
    check(len(sources) >= MIN_SEARCH_SOURCES,
          f"search-index covers only {len(sources)} sources"
          f" (< {MIN_SEARCH_SOURCES}): {sorted(sources)}")


def validate_stats(stats: dict) -> None:
    check("total_items" in stats, "stats must have total_items")
    check("sources" in stats, "stats must have sources")
    check("source_counts" in stats, "stats must have source_counts")
    check(isinstance(stats["source_counts"], dict), "stats.source_counts must be a dict")
    # 口径一致性：source_counts 与 sources 列表一致
    check(set(stats.get("sources", [])) == set(stats.get("source_counts", {})),
          "stats.sources and stats.source_counts keys must match")


def validate_summaries(summaries: dict) -> None:
    check(isinstance(summaries, dict), "summaries.json must be an object keyed by item id")
    empty = 0
    for iid, entry in summaries.items():
        check(isinstance(entry, dict), f"summaries[{iid}] must be an object")
        zh = entry.get("summary_zh")
        en = entry.get("summary_en")
        check(isinstance(zh, str), f"summaries[{iid}].summary_zh must be a string")
        check(isinstance(en, str), f"summaries[{iid}].summary_en must be a string")
        ih = entry.get("input_hash")
        if ih is not None:
            check(isinstance(ih, str) and len(ih) > 0,
                  f"summaries[{iid}].input_hash must be a non-empty string")
        if not (zh or "").strip():
            empty += 1
    if empty:
        print(f"[WARN] summaries.json 含 {empty} 条空摘要条目（回填中属正常，持续增多需关注）")


def validate_trends(trends: dict) -> None:
    check("generated_at" in trends, "trends must have generated_at")
    check("dates" in trends and isinstance(trends["dates"], list) and trends["dates"],
          "trends.dates must be a non-empty list")
    dates = trends["dates"]
    for d in dates:
        datetime.strptime(d, "%Y-%m-%d")
    check("topics" in trends and isinstance(trends["topics"], list),
          "trends.topics must be a list")
    for topic in trends["topics"]:
        check(isinstance(topic, dict), "trends topic must be an object")
        check(topic.get("keyword"), f"trends topic missing keyword: {topic}")
        check(isinstance(topic.get("count"), int) and topic["count"] > 0,
              f"trends topic {topic.get('keyword')} count must be a positive int")
        check(topic.get("trend") in TREND_VALUES,
              f"trends topic {topic.get('keyword')} has invalid trend: {topic.get('trend')!r}")
        heat = topic.get("heat_by_date")
        check(isinstance(heat, dict), f"trends topic {topic.get('keyword')} missing heat_by_date")
        for d in heat:
            check(d in dates,
                  f"trends topic {topic.get('keyword')} heat_by_date key {d} not in dates")
        check(isinstance(topic.get("sample_titles", []), list),
              f"trends topic {topic.get('keyword')} sample_titles must be a list")
        check(isinstance(topic.get("sources", []), list),
              f"trends topic {topic.get('keyword')} sources must be a list")


def validate_valid_tags(vt: dict) -> None:
    check("generated_at" in vt, "valid-tags must have generated_at")
    check(isinstance(vt.get("min_tag_items"), int), "valid-tags must have min_tag_items")
    check(isinstance(vt.get("min_domain_items"), int), "valid-tags must have min_domain_items")
    check(isinstance(vt.get("tags"), list) and all(isinstance(t, str) for t in vt["tags"]),
          "valid-tags.tags must be a list of strings")
    check(isinstance(vt.get("domains"), list) and all(isinstance(d, str) for d in vt["domains"]),
          "valid-tags.domains must be a list of strings")


def main() -> int:
    errors: list[str] = []

    def run(name: str, fn) -> None:
        print(f"[Validate] {name}")
        try:
            fn(load(name))
        except ValidationError as e:
            errors.append(f"{name}: {e}")
        except (json.JSONDecodeError, FileNotFoundError) as e:
            errors.append(f"{name}: {e}")

    run("feed.json", validate_feed)
    run("digest.json", validate_digest)
    run("search-index.json", validate_search_index)
    run("stats.json", validate_stats)
    run("summaries.json", validate_summaries)
    run("trends.json", validate_trends)
    run("valid-tags.json", validate_valid_tags)

    if errors:
        for e in errors:
            print(f"[FAIL] {e}")
        print("[Validate] FAILED")
        return 1
    print("[Validate] OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
