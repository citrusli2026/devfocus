#!/usr/bin/env python3
"""Fetch hot topics from V2EX (developer forum) via its index.xml feed.

V2EX 的 index.xml 实际是 Atom 格式（<entry>，非 RSS <item>），解析按命名空间无关处理，
同时兼容两种格式。条目时间统一转成 ISO 8601 落盘（aggregate._parse_time 可解析）。
抓取带重试，彻底失败或零条目时保留旧缓存（风格对齐 fetch_hn.py）。
"""
import hashlib
import json
import sys
import time
import urllib.error
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from pathlib import Path

OUT = Path(__file__).parent.parent / "2-raw" / "v2ex.json"
RSS = "https://www.v2ex.com/index.xml"

HEADERS = {"User-Agent": "DevFocus/1.0"}
MAX_ITEMS = 20


def _stable_id(title: str, link: str) -> str:
    """Generate stable ID from title+link hash."""
    raw = (title + link).encode()
    return hashlib.md5(raw).hexdigest()[:12]


def _fetch_xml(retries: int = 3, timeout: int = 30) -> str:
    for attempt in range(retries):
        try:
            req = urllib.request.Request(RSS, headers=HEADERS)
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                return resp.read().decode("utf-8", errors="replace")
        except (urllib.error.URLError, TimeoutError, OSError) as e:
            if attempt < retries - 1:
                wait = 2 ** attempt
                print(f"  [V2EX RETRY {attempt+1}/{retries}] {e}, waiting {wait}s...")
                time.sleep(wait)
            else:
                raise
    return ""  # unreachable, keeps type checkers happy


def _parse_pub_date(pub_date: str, fallback: str) -> str:
    """条目时间 → ISO 8601 (UTC)；解析失败用抓取时间兜底，保证 time 字段合法。

    兼容两种格式：RSS 的 RFC822 pubDate 和 Atom 的 ISO published/updated。
    """
    if pub_date:
        try:
            return parsedate_to_datetime(pub_date).astimezone(timezone.utc).isoformat()
        except (TypeError, ValueError):
            pass
        try:
            dt = datetime.fromisoformat(pub_date.replace("Z", "+00:00"))
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt.astimezone(timezone.utc).isoformat()
        except ValueError:
            pass
    return fallback


def _local(tag: str) -> str:
    """Strip XML namespace: '{http://www.w3.org/2005/Atom}entry' -> 'entry'."""
    return tag.rsplit("}", 1)[-1]


def _parse_entries(root: ET.Element) -> list[dict]:
    """Parse both RSS <item> and Atom <entry> elements (V2EX 实际返回 Atom)。"""
    entries = []
    for entry in root.iter():
        if _local(entry.tag) not in ("item", "entry"):
            continue
        title = link = pub_date = ""
        for child in entry:
            name = _local(child.tag)
            if name == "title":
                title = (child.text or "").strip()
            elif name == "link":
                # Atom: <link href="..."/>；RSS: <link>text</link>
                link = child.get("href") or (child.text or "").strip() or link
            elif name in ("pubDate", "published", "updated"):
                pub_date = pub_date or (child.text or "").strip()
        if title:
            entries.append({"title": title, "link": link, "pub_date": pub_date})
    return entries


def fetch():
    fetched_at = datetime.now(timezone.utc).isoformat()

    try:
        xml_data = _fetch_xml()
    except Exception as e:
        print(f"[V2EX ERROR] Fetch failed after retries: {e}", file=sys.stderr)
        if OUT.exists():
            print("[V2EX] Using cached data from previous run")
            return
        sys.exit(1)

    try:
        root = ET.fromstring(xml_data)
    except ET.ParseError as e:
        print(f"[V2EX ERROR] RSS/Atom parse failed: {e}", file=sys.stderr)
        if OUT.exists():
            print("[V2EX] Using cached data from previous run")
            return
        sys.exit(1)

    entries = _parse_entries(root)[:MAX_ITEMS]
    if not entries:
        # 解析成功但零条目，说明源结构又变了——保留旧缓存并报警，不覆盖好数据
        print("[V2EX ERROR] 0 entries parsed, feed format may have changed", file=sys.stderr)
        if OUT.exists():
            print("[V2EX] Using cached data from previous run")
            return
        sys.exit(1)

    items = []
    for rank, entry in enumerate(entries):
        items.append({
            "id": _stable_id(entry["title"], entry["link"]),
            "title": entry["title"],
            "url": entry["link"],
            "source": "v2ex",
            # V2EX feed 无任何互动指标，score 恒 0 会让该源在 search-index（按 score 取前 1000）
            # 和 quality_score 中没有存在感（与知乎 score=0 同类问题）；
            # 用榜单位次做代理分：第 1 名 300 分，逐名 -10（量级对齐中等 HN 条目）
            "score": max(300 - rank * 10, 10),
            "time": _parse_pub_date(entry["pub_date"], fetched_at),
            "tags": [],
        })

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps({"fetched_at": fetched_at, "source": "v2ex", "count": len(items), "items": items},
                              ensure_ascii=False, indent=2))
    print(f"[V2EX] {len(items)} topics -> {OUT}")


if __name__ == "__main__":
    fetch()
