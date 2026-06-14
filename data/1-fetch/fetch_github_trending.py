#!/usr/bin/env python3
from __future__ import annotations

"""GitHub Trending repos — HTML scrape with API fallback."""

import json
import sys
import urllib.request
import urllib.error
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path

URLS = {
    "daily": "https://github.com/trending?since=daily",
    "monthly": "https://github.com/trending?since=monthly",
}

# Fallback: GitHub search API (no auth needed, rate limit 10/min)
SEARCH_API = "https://api.github.com/search/repositories?q=created:>{date}&sort=stars&order=desc&per_page=30"


class TrendingParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.repos = []
        self._current = {}
        self._in_article = False
        self._in_h2 = False
        self._in_desc = False
        self._in_stars = False
        self._in_lang = False
        self._text_buf = ""

    def handle_starttag(self, tag, attrs):
        attrs_dict = dict(attrs)
        cls = attrs_dict.get("class", "") or ""
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
            elif tag == "a" and "Link--muted" in cls and "/stargazers" in (attrs_dict.get("href") or ""):
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


def fetch_html(url: str) -> list[dict]:
    req = urllib.request.Request(url, headers={
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) DevFocus/1.0",
        "Accept": "text/html",
    })
    with urllib.request.urlopen(req, timeout=15) as resp:
        html = resp.read().decode("utf-8", errors="replace")
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
    return repos


def fetch_api_fallback(period: str) -> list[dict]:
    """Fallback: use GitHub search API for recently created popular repos."""
    from datetime import timedelta
    now = datetime.now(timezone.utc)
    if period == "daily":
        date = (now - timedelta(days=1)).strftime("%Y-%m-%d")
    else:
        date = (now - timedelta(days=30)).strftime("%Y-%m-%d")

    url = SEARCH_API.format(date=date)
    req = urllib.request.Request(url, headers={
        "User-Agent": "DevFocus/1.0",
        "Accept": "application/vnd.github.v3+json",
    })
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode())
    except Exception as e:
        print(f"[GH] API fallback also failed: {e}", file=sys.stderr)
        return []

    repos = []
    for item in data.get("items", [])[:30]:
        repos.append({
            "full_name": item.get("full_name", ""),
            "name": item.get("name", ""),
            "url": item.get("html_url", ""),
            "description": item.get("description", "") or "",
            "stars_today": item.get("stargazers_count", 0),
            "source": "github_trending",
        })
    print(f"[GH] API fallback returned {len(repos)} repos for {period}")
    return repos


def main():
    output_dir = Path(__file__).resolve().parent.parent / "2-raw"
    output_dir.mkdir(parents=True, exist_ok=True)
    now = datetime.now(timezone.utc)

    for period, url in URLS.items():
        output_path = output_dir / f"gh_trending_{period}.json"
        print(f"[GH] Fetching {period} trending...")

        repos = []
        # Try HTML scrape first
        try:
            repos = fetch_html(url)
            print(f"[GH] HTML scrape: {len(repos)} repos")
        except Exception as e:
            print(f"[GH] HTML scrape failed: {e}")

        # Fallback to API if HTML failed or returned too few
        if len(repos) < 5:
            print(f"[GH] Trying API fallback for {period}...")
            repos = fetch_api_fallback(period)

        if repos:
            result = {
                "fetched_at": now.isoformat(),
                "source": "github_trending",
                "period": period,
                "count": len(repos),
                "items": repos,
            }
            output_path.write_text(json.dumps(result, indent=2, ensure_ascii=False))
            print(f"[GH] {period}: {len(repos)} repos → {output_path.name}")
        else:
            print(f"[GH] {period}: no data available")

    # Keep backward-compatible gh_trending.json (daily)
    daily_path = output_dir / "gh_trending_daily.json"
    compat_path = output_dir / "gh_trending.json"
    if daily_path.exists():
        import shutil
        shutil.copy2(daily_path, compat_path)


if __name__ == "__main__":
    main()
