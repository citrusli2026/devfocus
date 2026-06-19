#!/usr/bin/env python3
from __future__ import annotations

"""Fetch Zhihu (知乎) hot list via tophub.today."""

import json
import re
import sys
import time
import urllib.request
import urllib.error
from datetime import datetime, timezone
from pathlib import Path

TOPHUB_URL = "https://tophub.today/n/mproPpoq6O"
TOP_N = 10


def fetch_hot_list() -> list[dict]:
    """Fetch Zhihu hot list from tophub.today."""
    req = urllib.request.Request(TOPHUB_URL, headers={
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
    })

    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            html = resp.read().decode("utf-8")
    except Exception as e:
        print(f"[Zhihu] Fetch error: {e}", file=sys.stderr)
        return []

    # Extract links with titles
    links = re.findall(
        r'<a[^>]*href="(https://www\.zhihu\.com/question/\d+)"[^>]*target="_blank"[^>]*>([^<]+)</a>',
        html
    )

    items = []
    for url, title in links[:TOP_N]:
        title = title.strip()
        if not title or len(title) < 5:
            continue
        # Extract question ID
        qid = re.search(r'/question/(\d+)', url)
        items.append({
            "id": f"zhihu-{qid.group(1)}" if qid else f"zhihu-{hash(title)}",
            "title": title,
            "url": url,
            "description": "",
            "source": "zhihu",
            "score": 0,
            "comments": 0,
            "author": "",
            "time": datetime.now(timezone.utc).isoformat(),
            "tags": ["zhihu"],
        })

    return items


def main():
    output_dir = Path(__file__).resolve().parent.parent / "2-raw"
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / "zhihu_daily.json"

    print("[Zhihu] Fetching hot list...")
    items = fetch_hot_list()
    print(f"[Zhihu] Got {len(items)} items")

    result = {
        "fetched_at": datetime.now(timezone.utc).isoformat(),
        "source": "zhihu",
        "count": len(items),
        "items": items,
    }
    output_path.write_text(json.dumps(result, indent=2, ensure_ascii=False))
    print(f"[Zhihu] Saved to {output_path.name}")


if __name__ == "__main__":
    main()
