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


def load_raw(filename: str) -> dict | None:
    path = RAW_DIR / filename
    if not path.exists():
        return None
    return json.loads(path.read_text())


def aggregate_hn(data: dict) -> list[dict]:
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


def aggregate_github(data: dict, period: str = "daily") -> list[dict]:
    items = []
    for r in data.get("items", []):
        items.append({
            "id": f"gh-{period}-{r['full_name'].replace('/', '-')}",
            "title": r["full_name"],
            "url": r.get("url", ""),
            "description": r.get("description", ""),
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
    by_source: dict[str, list[dict]] = {}
    for item in items:
        by_source.setdefault(item["source"], []).append(item)
    result = []
    for source_items in by_source.values():
        source_items.sort(key=lambda x: x["score"], reverse=True)
        result.extend(source_items[:n])
    result.sort(key=lambda x: x["score"], reverse=True)
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


def save_snapshot(items: list[dict], now: datetime):
    HISTORY_DIR.mkdir(parents=True, exist_ok=True)
    path = HISTORY_DIR / f"{date_key(now)}.json"
    path.write_text(json.dumps({"date": date_key(now), "fetched_at": now.isoformat(), "items": items}, indent=2, ensure_ascii=False))
    print(f"[AGG] Snapshot: {len(items)} items → {path.name}")


def dedupe_by_title(items: list[dict]) -> list[dict]:
    """Deduplicate items with same title across sources, keeping highest score."""
    seen: dict[str, dict] = {}
    for item in items:
        key = item["title"].lower().strip()
        if key not in seen or item["score"] > seen[key]["score"]:
            seen[key] = item
    return list(seen.values())


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
        for item in kr_data:
            kr_items.append({
                "id": f"36kr-{item['id']}",
                "title": item["title"],
                "url": item["url"],
                "description": "",
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
        for item in iq_data:
            iq_items.append({
                "id": f"infoq-{item['id']}",
                "title": item["title"],
                "url": item["url"],
                "description": "",
                "source": "infoq",
                "score": item.get("score", 0),
                "comments": 0,
                "author": "",
                "time": item.get("time", ""),
                "tags": item.get("tags", []),
            })
        fresh_items.extend(iq_items)
        print(f"[AGG] InfoQ: {len(iq_items)} items")

    # Save snapshot
    save_snapshot(fresh_items, now)

    # Load history for period reports
    history_items = load_history()
    history_items.sort(key=lambda x: x["score"], reverse=True)
    print(f"[AGG] History: {len(history_items)} unique items")

    # --- Build digests ---

    # Daily: top N per source from fresh data
    daily_items = pick_top_per_source(fresh_items, DAILY_PER_SOURCE)

    # Monthly: top N per source from history (past 30 days)
    monthly_hn = [i for i in history_items if i["source"] == "hackernews" and _parse_time(i) >= now - timedelta(days=30)]
    monthly_gh = [i for i in fresh_items if i.get("gh_period") == "monthly"]
    monthly_all = dedupe_by_title(monthly_hn + monthly_gh)
    monthly_all.sort(key=lambda x: x["score"], reverse=True)
    monthly_items = pick_top_per_source(monthly_all, MONTHLY_PER_SOURCE)

    month_ago = now - timedelta(days=30)
    sources = sorted({i["source"] for i in history_items})

    digest = {
        "generated_at": now.isoformat(),
        "daily": {"date": today_key, "items": daily_items, "count": len(daily_items)},
        "monthly": {"start": date_key(month_ago), "end": today_key, "items": monthly_items, "count": len(monthly_items)},
        "sources": sources,
        "total_items": len(history_items),
    }

    FINAL_DIR.joinpath("digest.json").write_text(json.dumps(digest, indent=2, ensure_ascii=False))
    print(f"[AGG] Digest: daily={len(daily_items)} monthly={len(monthly_items)}")

    # Full feed
    by_date: dict[str, list[dict]] = {}
    for item in history_items:
        k = date_key(_parse_time(item))
        by_date.setdefault(k, []).append(item)

    FINAL_DIR.joinpath("feed.json").write_text(json.dumps({
        "generated_at": now.isoformat(),
        "items": history_items,
        "by_date": {k: v for k, v in sorted(by_date.items(), reverse=True)},
    }, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
