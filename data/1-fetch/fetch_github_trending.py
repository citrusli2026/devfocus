#!/usr/bin/env python3
from __future__ import annotations

"""GitHub Trending repos fetcher. Parses the trending page HTML."""

import json
import re
import sys
import urllib.request
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path

TRENDING_URL = "https://github.com/trending?since=daily"


class TrendingParser(HTMLParser):
    """Minimal HTML parser for GitHub trending page."""

    def __init__(self):
        super().__init__()
        self.repos = []
        self._current = {}
        self._in_article = False
        self._in_h2 = False
        self._in_desc = False
        self._in_stars = False
        self._in_lang = False
        self._capture_text = False
        self._text_buf = ""

    def handle_starttag(self, tag, attrs):
        attrs_dict = dict(attrs)
        cls = attrs_dict.get("class", "")

        if tag == "article" and "Box-row" in cls:
            self._in_article = True
            self._current = {}

        if self._in_article:
            if tag == "h2" and "h3" in cls:
                self._in_h2 = True
                self._text_buf = ""
            elif tag == "a" and self._in_h2:
                href = attrs_dict.get("href", "").strip("/")
                if href and "/" in href:
                    self._current["full_name"] = href
                    self._current["url"] = f"https://github.com/{href}"
            elif tag == "p" and "col-9" in cls:
                self._in_desc = True
                self._text_buf = ""
            elif tag == "a" and "Link--muted" in cls and "/stargazers" in attrs_dict.get("href", ""):
                self._in_stars = True
                self._text_buf = ""
            elif tag == "span" and "repo-language-color" in cls:
                self._in_lang = True
            elif tag == "span" and self._in_lang:
                self._text_buf = ""

    def handle_endtag(self, tag):
        if tag == "h2" and self._in_h2:
            self._in_h2 = False
            name = " ".join(self._text_buf.split()).strip()
            if name:
                self._current["name"] = name
        elif tag == "p" and self._in_desc:
            self._in_desc = False
            self._current["description"] = " ".join(self._text_buf.split()).strip()
        elif tag == "a" and self._in_stars:
            self._in_stars = False
            stars = self._text_buf.strip().replace(",", "")
            if stars.isdigit():
                self._current["stars_today"] = int(stars)
        elif tag == "span" and self._in_lang:
            self._in_lang = False
        elif tag == "article" and self._in_article:
            self._in_article = False
            if self._current.get("full_name"):
                self.repos.append(self._current)
            self._current = {}

    def handle_data(self, data):
        if self._in_h2 or self._in_desc or self._in_stars or self._in_lang:
            self._text_buf += data


def main():
    output_dir = Path(__file__).resolve().parent.parent / "2-raw"
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / "gh_trending.json"

    print("[GH] Fetching GitHub trending repos...")
    req = urllib.request.Request(TRENDING_URL, headers={
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) DevPulse/1.0",
        "Accept": "text/html",
    })

    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            html = resp.read().decode("utf-8", errors="replace")
    except Exception as e:
        print(f"[ERROR] Failed to fetch trending: {e}", file=sys.stderr)
        sys.exit(1)

    parser = TrendingParser()
    parser.feed(html)

    repos = []
    for r in parser.repos:
        repos.append({
            "full_name": r.get("full_name", ""),
            "name": r.get("name", r.get("full_name", "")),
            "url": r.get("url", ""),
            "description": r.get("description", ""),
            "stars_today": r.get("stars_today", 0),
            "source": "github_trending",
        })

    result = {
        "fetched_at": datetime.now(timezone.utc).isoformat(),
        "source": "github_trending",
        "count": len(repos),
        "items": repos,
    }

    output_path.write_text(json.dumps(result, indent=2, ensure_ascii=False))
    print(f"[GH] Saved {len(repos)} repos to {output_path}")


if __name__ == "__main__":
    main()
