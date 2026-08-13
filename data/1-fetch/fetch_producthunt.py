#!/usr/bin/env python3
from __future__ import annotations

"""Fetch Product Hunt daily top posts via GraphQL API."""

import json
import os
import sys
import time
import urllib.request
import urllib.error
from datetime import datetime, timezone, timedelta
from pathlib import Path

from _common import html_to_text

BASE_DIR = Path(__file__).resolve().parent.parent
API_URL = "https://api.producthunt.com/v2/api/graphql"
TOP_N = 5  # 每天取 Top N 产品


def get_token() -> str:
    """Get PH token from env or .ph_token file."""
    token = os.environ.get("PH_TOKEN", "")
    if not token:
        token_file = BASE_DIR / ".ph_token"
        if token_file.exists():
            token = token_file.read_text().strip()
    if not token:
        print("[ProductHunt] No PH_TOKEN found", file=sys.stderr)
        return ""
    return token


def query_posts(token: str, date: str) -> list[dict]:
    """Query PH GraphQL API for top posts on a given date.

    date format: YYYY-MM-DD
    """
    posted_after = f"{date}T00:00:00Z"
    posted_before_date = datetime.strptime(date, "%Y-%m-%d") + timedelta(days=1)
    posted_before = posted_before_date.strftime("%Y-%m-%dT00:00:00Z")

    query = """{
      posts(order: VOTES, postedAfter: "%s", postedBefore: "%s", first: %d) {
        edges {
          node {
            id
            name
            tagline
            description
            votesCount
            commentsCount
            url
            website
          }
        }
      }
    }""" % (posted_after, posted_before, TOP_N)

    body = json.dumps({"query": query}).encode()
    req = urllib.request.Request(API_URL, data=body, headers={
        "Content-Type": "application/json",
        "User-Agent": "DevFocus/1.0 (https://devfocus.cc)",
        "Authorization": f"Bearer {token}",
    })

    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode())
            edges = data.get("data", {}).get("posts", {}).get("edges", [])
            return [e["node"] for e in edges]
    except Exception as e:
        print(f"[ProductHunt] API error for {date}: {e}", file=sys.stderr)
        return []


def main():
    token = get_token()
    output_dir = BASE_DIR / "2-raw"
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / "producthunt_daily.json"

    if not token:
        # 无 token：保留旧缓存（新鲜空文件会覆盖好数据，且新鲜时间戳会绕过
        # aggregate 的 STALE_HOURS 缺席检测导致源静默消失）
        print("[ProductHunt] No PH_TOKEN found", file=sys.stderr)
        if output_path.exists():
            old = json.loads(output_path.read_text())
            if old.get("items"):
                print(f"[ProductHunt] Keeping cached {len(old['items'])} items (no token)",
                      file=sys.stderr)
                return
        result = {"fetched_at": datetime.now(timezone.utc).isoformat(),
                  "source": "producthunt", "count": 0, "items": []}
        output_path.write_text(json.dumps(result, indent=2, ensure_ascii=False))
        return

    all_items = []
    today = datetime.now(timezone.utc).date()

    # Fetch last 3 days
    for offset in range(3):
        date = (today - timedelta(days=offset + 1)).strftime("%Y-%m-%d")
        print(f"[ProductHunt] Fetching {date}...")
        posts = query_posts(token, date)

        for post in posts:
            # Clean PH tracking params from URL（post['url'] 缺失时用 get 防御，
            # 避免字段缺失导致整个脚本崩溃——此前无降级）
            url = (post.get("url") or "").split("?")[0] if "?" in (post.get("url") or "") else post.get("url", "")
            website = post.get("website", "") or ""
            if "?" in website:
                website = website.split("?")[0]

            all_items.append({
                "id": f"ph-{post['id']}",
                "title": post["name"],
                "url": website or url,
                "description": post.get("tagline", "")[:200],
                "content": html_to_text(post.get("description") or "", max_chars=2000),
                "source": "producthunt",
                "score": post.get("votesCount", 0),
                "comments": post.get("commentsCount", 0),
                "author": "",
                "time": f"{date}T12:00:00+00:00",
                "tags": ["product-hunt"],
            })

        if offset < 2:
            time.sleep(0.5)

    print(f"[ProductHunt] Total: {len(all_items)} items")

    if not all_items and output_path.exists():
        # 全部 3 天查询都失败：保留旧缓存，避免空文件覆盖 + 绕过缺席检测
        old = json.loads(output_path.read_text())
        if old.get("items"):
            print(f"[ProductHunt] All API queries failed, keeping cached {len(old['items'])} items",
                  file=sys.stderr)
            return

    result = {
        "fetched_at": datetime.now(timezone.utc).isoformat(),
        "source": "producthunt",
        "count": len(all_items),
        "items": all_items,
    }
    output_path = output_dir / "producthunt_daily.json"
    output_path.write_text(json.dumps(result, indent=2, ensure_ascii=False))
    print(f"[ProductHunt] Saved to {output_path.name}")


if __name__ == "__main__":
    main()
