#!/usr/bin/env python3
from __future__ import annotations

"""Aggregate raw data → digest with differentiated time periods."""

import json
from datetime import datetime, timezone, timedelta
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
RAW_DIR = BASE_DIR / "2-raw"
FINAL_DIR = BASE_DIR / "4-final"
HISTORY_DIR = BASE_DIR / "5-history"
DAILY_PER_SOURCE = 10
MONTHLY_PER_SOURCE = 10

# raw 数据超过该时长未更新即视为源"缺席"，不进日榜并在 digest.missing_sources 标注
STALE_HOURS = 36

# 各数据源对应的 2-raw 文件（github_trending 三个周期文件同批抓取，以 daily 文件为准）
SOURCE_RAW_FILES = {
    "hackernews": "hn_top_stories.json",
    "github_trending": "gh_trending_daily.json",
    "producthunt": "producthunt_daily.json",
    "juejin": "juejin_daily.json",
    "zhihu": "zhihu_daily.json",
    "36kr": "36kr.json",
    "infoq": "infoq.json",
    "v2ex": "v2ex.json",
}


def load_raw(filename: str) -> dict | None:
    path = RAW_DIR / filename
    if not path.exists():
        return None
    return json.loads(path.read_text())


def raw_freshness(filename: str, data) -> datetime | None:
    """raw 数据的抓取时间：优先 fetched_at 字段；裸 list（36kr/infoq）无该字段，用文件 mtime 兜底。"""
    if isinstance(data, dict):
        fetched_at = data.get("fetched_at")
        if fetched_at:
            try:
                return datetime.fromisoformat(str(fetched_at).replace("Z", "+00:00"))
            except ValueError:
                pass
    try:
        return datetime.fromtimestamp((RAW_DIR / filename).stat().st_mtime, tz=timezone.utc)
    except OSError:
        return None


def find_missing_sources(now: datetime) -> list[str]:
    """raw 文件缺失、不可解析或超过 STALE_HOURS 未更新的源视为缺席。"""
    missing = []
    cutoff = now - timedelta(hours=STALE_HOURS)
    for source, filename in SOURCE_RAW_FILES.items():
        path = RAW_DIR / filename
        if not path.exists():
            missing.append(source)
            continue
        try:
            data = json.loads(path.read_text())
        except Exception:
            missing.append(source)
            continue
        ts = raw_freshness(filename, data)
        if ts is None or ts < cutoff:
            missing.append(source)
    return sorted(missing)


def aggregate_hn(data: dict) -> list[dict]:
    items = []
    for s in data.get("items", []):
        items.append({
            "id": f"hn-{s['id']}",
            "title": s["title"],
            "url": s.get("url") or s.get("hn_url", ""),
            "description": "",
            "content": s.get("content", ""),  # 摘要内部素材，不进前端产出
            "source": "hackernews",
            "score": s.get("score", 0),
            "comments": s.get("descendants", 0),
            "author": s.get("by", ""),
            "time": s.get("time_iso", ""),
            "tags": [],
        })
    return items


def aggregate_github(data: dict, period: str = "daily") -> list[dict]:
    items = []
    for r in data.get("items", []):
        items.append({
            "id": f"gh-{period}-{r['full_name'].replace('/', '-')}",
            "title": r["full_name"],
            "url": r.get("url", ""),
            "description": r.get("description", ""),
            "readme": r.get("readme", ""),  # 摘要阶段的全文素材，不进前端产出
            "source": "github_trending",
            "score": r.get("stars_today", 0),
            "comments": 0,
            "author": r["full_name"].split("/")[0] if "/" in r["full_name"] else "",
            "time": data.get("fetched_at", ""),
            "tags": [],
            "gh_period": period,
        })
    return items


def aggregate_producthunt(data: dict) -> list[dict]:
    items = []
    for s in data.get("items", []):
        items.append({
            "id": s.get("id", f"ph-{hash(s.get('title', ''))}"),
            "title": s.get("title", ""),
            "url": s.get("url", ""),
            "description": s.get("description", ""),
            "source": "producthunt",
            "score": s.get("score", 0),
            "comments": s.get("comments", 0),
            "author": s.get("author", ""),
            "time": s.get("time", ""),
            "tags": s.get("tags", []),
        })
    return items



def pick_top_per_source(items: list[dict], n: int) -> list[dict]:
    """按源各取 top n，跨源排序使用源内归一化分。

    各源 score 量纲差异巨大（zhihu 万热度可达 2 千万级、v2ex 榜位代理分
    10~300、HN 几百、GH stars_today 几千），直接按原始分跨源排序会被
    大量纲源霸榜。源内选取仍用原始分，最终合并排序用 score/源内最大值。
    """
    by_source: dict[str, list[dict]] = {}
    for item in items:
        by_source.setdefault(item["source"], []).append(item)
    result = []
    for source_items in by_source.values():
        source_items.sort(key=lambda x: x["score"], reverse=True)
        result.extend(source_items[:n])
    max_by_source = {
        src: max((i.get("score", 0) for i in lst), default=1) or 1
        for src, lst in by_source.items()
    }

    def normalized_key(item: dict) -> float:
        return item.get("score", 0) / max_by_source.get(item["source"], 1)

    result.sort(key=normalized_key, reverse=True)
    return result


def filter_by_age(items: list[dict], days: int, now: datetime) -> list[dict]:
    cutoff = now - timedelta(days=days)
    return [i for i in items if _parse_time(i) >= cutoff]


def _parse_time(item: dict) -> datetime:
    t = item.get("time", "")
    if isinstance(t, (int, float)) and t > 0:
        # Unix timestamp (seconds or milliseconds)
        if t > 1e12:
            t = t / 1000
        return datetime.fromtimestamp(t, tz=timezone.utc)
    try:
        return datetime.fromisoformat(str(t).replace("Z", "+00:00"))
    except (ValueError, KeyError):
        return datetime.min.replace(tzinfo=timezone.utc)


def date_key(dt: datetime) -> str:
    return dt.strftime("%Y-%m-%d")


def load_history() -> list[dict]:
    all_items: dict[str, dict] = {}
    if not HISTORY_DIR.exists():
        return []
    for f in sorted(HISTORY_DIR.glob("*.json")):
        try:
            data = json.loads(f.read_text())
            for item in data.get("items", []):
                all_items[item["id"]] = item
        except Exception:
            continue
    return list(all_items.values())


def load_first_seen_map() -> dict[str, str]:
    """Scan history snapshots to find the earliest date each item ID appeared."""
    first_seen: dict[str, str] = {}
    if not HISTORY_DIR.exists():
        return first_seen
    for f in sorted(HISTORY_DIR.glob("*.json")):
        date_str = f.stem  # e.g. "2026-06-20"
        try:
            data = json.loads(f.read_text())
            for item in data.get("items", []):
                iid = item["id"]
                if iid not in first_seen:
                    first_seen[iid] = date_str
        except Exception:
            continue
    return first_seen


def save_snapshot(items: list[dict], digest_items: list[dict], now: datetime):
    HISTORY_DIR.mkdir(parents=True, exist_ok=True)
    path = HISTORY_DIR / f"{date_key(now)}.json"
    path.write_text(json.dumps({
        "date": date_key(now),
        "fetched_at": now.isoformat(),
        "items": items,
        "digest_items": digest_items,
    }, indent=2, ensure_ascii=False))
    print(f"[AGG] Snapshot: {len(items)} items, {len(digest_items)} digest items → {path.name}")


def cleanup_old_snapshots(days: int = 30):
    """Remove history snapshots older than `days` days."""
    if not HISTORY_DIR.exists():
        return
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    removed = 0
    for f in HISTORY_DIR.glob("*.json"):
        try:
            date_str = f.stem.split("-")[0:3]
            if len(date_str) != 3:
                continue
            file_date = datetime(int(date_str[0]), int(date_str[1]), int(date_str[2]), tzinfo=timezone.utc)
            if file_date < cutoff:
                f.unlink()
                removed += 1
        except Exception:
            continue
    if removed:
        print(f"[AGG] Removed {removed} snapshots older than {days} days")


def dedupe_by_title(items: list[dict]) -> list[dict]:
    """Deduplicate items with same title across sources, keeping highest score."""
    seen: dict[str, dict] = {}
    for item in items:
        key = item["title"].lower().strip()
        if key not in seen or item["score"] > seen[key]["score"]:
            seen[key] = item
    return list(seen.values())


def strip_internal(items: list[dict]) -> None:
    """移除摘要内部素材字段（readme/content），不进前端产出，原地修改。"""
    for it in items:
        it.pop("readme", None)
        it.pop("content", None)


def main():
    FINAL_DIR.mkdir(parents=True, exist_ok=True)
    now = datetime.now(timezone.utc)
    today_key = date_key(now)

    # --- Load raw data ---
    fresh_items: list[dict] = []

    # HN (has historical data from 200 fetches)
    hn_data = load_raw("hn_top_stories.json")
    if hn_data:
        hn_items = aggregate_hn(hn_data)
        fresh_items.extend(hn_items)
        print(f"[AGG] HN: {len(hn_items)} items")

    # GitHub — use period-specific files
    for period in ["daily", "weekly", "monthly"]:
        gh_data = load_raw(f"gh_trending_{period}.json")
        if gh_data:
            gh_items = aggregate_github(gh_data, period)
            fresh_items.extend(gh_items)
            print(f"[AGG] GitHub {period}: {len(gh_items)} items")

    # Product Hunt
    ph_data = load_raw("producthunt_daily.json")
    if ph_data:
        ph_items = aggregate_producthunt(ph_data)
        fresh_items.extend(ph_items)
        print(f"[AGG] Product Hunt: {len(ph_items)} items")

    # Juejin (掘金)
    jj_data = load_raw("juejin_daily.json")
    if jj_data:
        jj_items = jj_data.get("items", [])
        fresh_items.extend(jj_items)
        print(f"[AGG] Juejin: {len(jj_items)} items")

    # Zhihu (知乎)
    zh_data = load_raw("zhihu_daily.json")
    if zh_data:
        zh_items = zh_data.get("items", [])
        fresh_items.extend(zh_items)
        print(f"[AGG] Zhihu: {len(zh_items)} items")

    # 36Kr (36氪)
    kr_data = load_raw("36kr.json")
    if kr_data:
        kr_items = []
        # 兼容历史裸 list 格式；新格式为 {fetched_at, source, count, items}
        raw_list = kr_data if isinstance(kr_data, list) else kr_data.get("items", [])
        for item in raw_list:
            kr_items.append({
                "id": f"36kr-{item['id']}",
                "title": item["title"],
                "url": item["url"],
                "description": "",
                "content": item.get("content", ""),  # 摘要内部素材，不进前端产出
                "source": "36kr",
                "score": item.get("score", 0),
                "comments": 0,
                "author": "",
                "time": item.get("time", ""),
                "tags": item.get("tags", []),
            })
        fresh_items.extend(kr_items)
        print(f"[AGG] 36Kr: {len(kr_items)} items")

    # InfoQ (InfoQ China)
    iq_data = load_raw("infoq.json")
    if iq_data:
        iq_items = []
        # 兼容历史裸 list 格式；新格式为 {fetched_at, source, count, items}
        raw_list = iq_data if isinstance(iq_data, list) else iq_data.get("items", [])
        for item in raw_list:
            iq_items.append({
                "id": f"infoq-{item['id']}",
                "title": item["title"],
                "url": item["url"],
                "description": "",
                "content": item.get("content", ""),  # 摘要内部素材，不进前端产出
                "source": "infoq",
                "score": item.get("score", 0),
                "comments": 0,
                "author": "",
                "time": item.get("time", ""),
                "tags": item.get("tags", []),
            })
        fresh_items.extend(iq_items)
        print(f"[AGG] InfoQ: {len(iq_items)} items")

    # V2EX
    v2_data = load_raw("v2ex.json")
    if v2_data:
        v2_items = []
        raw_items = v2_data.get("items", v2_data if isinstance(v2_data, list) else [])
        for item in raw_items:
            v2_items.append({
                "id": f"v2ex-{item['id']}",
                "title": item.get("title", ""),
                "url": item.get("url", ""),
                "description": "",
                "content": item.get("content", ""),  # 摘要内部素材，不进前端产出
                "source": "v2ex",
                "score": item.get("score", 0),
                "comments": 0,
                "author": "",
                "time": item.get("time", ""),
                "tags": item.get("tags", []),
            })
        fresh_items.extend(v2_items)
        print(f"[AGG] V2EX: {len(v2_items)} items")

    # --- Freshness check: 缺席源（raw 缺失或超过 STALE_HOURS 未更新）不进日榜 ---
    missing_sources = find_missing_sources(now)
    if missing_sources:
        print(f"[AGG] Missing sources (raw absent or stale >{STALE_HOURS}h): {', '.join(missing_sources)}")

    # Load first_seen from history (before adding today's snapshot)
    first_seen_map = load_first_seen_map()
    today_key_str = date_key(now)
    for item in fresh_items:
        iid = item["id"]
        if iid in first_seen_map:
            item["first_seen"] = first_seen_map[iid]
        else:
            item["first_seen"] = today_key_str

    # Build daily digest before saving snapshot so digest_items can be stored
    # 日榜只取 GitHub daily 条目（monthly 与 daily 同 source，需先按 gh_period 隔开），
    # 并按标题去重，避免同一仓库以 gh-daily-* / gh-monthly-* 重复出现
    daily_pool = [i for i in fresh_items
                  if i.get("gh_period") in (None, "daily") and i["source"] not in missing_sources]
    daily_items = pick_top_per_source(dedupe_by_title(daily_pool), DAILY_PER_SOURCE)

    # Save snapshot (full items + digest items)
    save_snapshot(fresh_items, daily_items, now)

    # Load history for period reports
    history_items = load_history()
    # 兜底回填 first_seen：今日快照已带该字段，更早日期的历史条目按首次出现日期补齐
    for item in history_items:
        item.setdefault("first_seen", first_seen_map.get(item["id"], today_key_str))
    history_items.sort(key=lambda x: x["score"], reverse=True)
    print(f"[AGG] History: {len(history_items)} unique items")

    # --- Build digests ---

    # Monthly: 全源 30 天窗口，与日榜一致按源取 top N（含今日快照在内的 history）
    month_ago = now - timedelta(days=30)
    monthly_pool = dedupe_by_title([i for i in history_items if _parse_time(i) >= month_ago])
    monthly_items = pick_top_per_source(monthly_pool, MONTHLY_PER_SOURCE)
    strip_internal(monthly_items)  # readme/content 仅供摘要，不进 digest/feed 产出

    sources = sorted({i["source"] for i in history_items})

    digest = {
        "generated_at": now.isoformat(),
        "daily": {"date": today_key, "items": daily_items, "count": len(daily_items)},
        "monthly": {"start": date_key(month_ago), "end": today_key, "items": monthly_items, "count": len(monthly_items)},
        "sources": sources,
        "missing_sources": missing_sources,
        "total_items": len(history_items),
    }

    FINAL_DIR.joinpath("digest.json").write_text(json.dumps(digest, indent=2, ensure_ascii=False))
    print(f"[AGG] Digest: daily={len(daily_items)} monthly={len(monthly_items)}")

    # Full feed
    strip_internal(history_items)  # readme/content 仅供摘要，不进 feed 产出
    by_date: dict[str, list[dict]] = {}
    for item in history_items:
        k = date_key(_parse_time(item))
        by_date.setdefault(k, []).append(item)

    FINAL_DIR.joinpath("feed.json").write_text(json.dumps({
        "generated_at": now.isoformat(),
        "items": history_items,
        "by_date": {k: v for k, v in sorted(by_date.items(), reverse=True)},
    }, indent=2, ensure_ascii=False))

    cleanup_old_snapshots(days=30)

    # digest-meta.json：轻量元数据（来源列表/日期/可用归档日），
    # 供前端 Footer/About/归档链接存在性兜底使用——
    # 避免全站每个页面打包 digest.json（223KB，含 80 条完整条目）
    history_dates = sorted(
        f.stem for f in HISTORY_DIR.glob("*.json") if len(f.stem) == 10
    )
    meta = {
        "generated_at": now.isoformat(timespec="seconds"),
        "date": today_key,
        "count": len(daily_items),
        "sources": sources,
        "history_dates": history_dates,
    }
    FINAL_DIR.joinpath("digest-meta.json").write_text(
        json.dumps(meta, indent=2, ensure_ascii=False))
    print(f"[AGG] Digest meta: {len(history_dates)} archive dates")


if __name__ == "__main__":
    main()
