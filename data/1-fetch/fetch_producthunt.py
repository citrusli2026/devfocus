#!/usr/bin/env python3
from __future__ import annotations

"""Fetch Product Hunt daily top posts via RSS feed."""

import json
import time
import urllib.request
import urllib.error
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path

RSS_URL = "https://raw.githubusercontent.com/headllines/producthunt-daily-rss/master/rss.xml"
HEADERS = {
    "User-Agent": "DevFocus/1.0 (https://devfocus.cc)",
    "Accept": "application/rss+xml, application/xml, text/xml",
}


def fetch_rss(url: str, timeout: int = 15, retries: int = 3) -> str | None:
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, headers=HEADERS)
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                return resp.read().decode("utf-8")
        except (urllib.error.URLError, TimeoutError, OSError) as e:
            if attempt < retries - 1:
                time.sleep(2 ** attempt)
            else:
                print(f"[ProductHunt] Failed to fetch RSS: {e}", file=__import__("sys").stderr)
                return None


def parse_rss(xml_text: str) -> list[dict]:
    """Parse RSS XML and extract items."""
    items = []
    try:
        root = ET.fromstring(xml_text)
        channel = root.find("channel")
        if channel is None:
            return items
        
        for item in channel.findall("item"):
            title = item.findtext("title", "").strip()
            link = item.findtext("link", "").strip()
            description = item.findtext("description", "").strip()
            pub_date = item.findtext("pubDate", "").strip()
            
            # Extract PH-specific fields from description or use defaults
            # RSS description typically contains tagline + link
            tagline = description if description else title
            
            # Try to parse pubDate
            try:
                # RFC 822 format: "Mon, 18 Jun 2026 00:00:00 +0000"
                from email.utils import parsedate_to_datetime
                dt = parsedate_to_datetime(pub_date)
            except (ValueError, TypeError):
                dt = datetime.now(timezone.utc)
            
            # Extract product name from link (e.g., /products/xxx)
            product_name = ""
            if "/products/" in link:
                product_name = link.split("/products/")[-1].split("?")[0].split("/")[0]
            
            items.append({
                "id": f"ph-{product_name}" if product_name else f"ph-{hash(title)}",
                "title": title,
                "url": link,
                "description": tagline[:200],
                "source": "producthunt",
                "score": 0,  # RSS doesn't provide votes
                "comments": 0,
                "author": "",
                "time": dt.isoformat(),
                "tags": ["product-hunt"],
            })
    except ET.ParseError as e:
        print(f"[ProductHunt] XML parse error: {e}", file=__import__("sys").stderr)
    
    return items


def main():
    output_dir = Path(__file__).resolve().parent.parent / "2-raw"
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / "producthunt_daily.json"

    print("[ProductHunt] Fetching RSS feed...")
    xml_text = fetch_rss(RSS_URL)
    if not xml_text:
        print("[ProductHunt] No data fetched", file=__import__("sys").stderr)
        # Write empty result
        result = {
            "fetched_at": datetime.now(timezone.utc).isoformat(),
            "source": "producthunt",
            "count": 0,
            "items": [],
        }
        output_path.write_text(json.dumps(result, indent=2, ensure_ascii=False))
        return

    items = parse_rss(xml_text)
    print(f"[ProductHunt] Parsed {len(items)} items from RSS")

    result = {
        "fetched_at": datetime.now(timezone.utc).isoformat(),
        "source": "producthunt",
        "count": len(items),
        "items": items,
    }
    output_path.write_text(json.dumps(result, indent=2, ensure_ascii=False))
    print(f"[ProductHunt] Total: {len(items)} items → {output_path.name}")


if __name__ == "__main__":
    main()
