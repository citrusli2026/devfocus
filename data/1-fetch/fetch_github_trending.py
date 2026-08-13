#!/usr/bin/env python3
from __future__ import annotations

"""GitHub Trending repos — HTML scrape with API fallback."""

import json
import re
import sys
import urllib.request
import urllib.error
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path

URLS = {
    "daily": "https://github.com/trending?since=daily",
    "monthly": "https://github.com/trending?since=monthly",
}

# Fallback: GitHub search API (no auth needed, rate limit 10/min)
SEARCH_API = "https://api.github.com/search/repositories?q=created:>{date}&sort=stars&order=desc&per_page=30"

# README 抓取：raw.githubusercontent 无需 auth，HEAD 跟随默认分支；
# 大小写/后缀变体逐个尝试，失败视为无 README
README_VARIANTS = ("README.md", "readme.md", "README.rst", "readme.rst")
README_MAX_CHARS = 2000


class TrendingParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.repos = []
        self._current = {}
        self._in_article = False
        self._in_h2 = False
        self._in_desc = False
        self._in_stars_total = False
        self._in_stars_today = False
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
                # /stargazers 链接里的数字是仓库总 star 数，不是当日新增
                self._in_stars_total = True
                self._text_buf = ""
            elif tag == "span" and "float-sm-right" in cls:
                # 卡片右下角 "N stars today / this month"，周期内新增 star 数
                self._in_stars_today = True
                self._text_buf = ""
            elif tag == "span" and attrs_dict.get("itemprop") == "programmingLanguage":
                # 语言名：<span itemprop="programmingLanguage">Python</span>。
                # 颜色圆点 span（repo-language-color）只作装饰，不能拿它的
                # 闭合来驱动捕获（此前语言解析因此是死代码，从未产出字段）
                self._in_lang = True
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
        elif tag == "a" and self._in_stars_total:
            self._in_stars_total = False
            stars = self._text_buf.strip().replace(",", "")
            if stars.isdigit():
                self._current["stars_total"] = int(stars)
        elif tag == "span" and self._in_stars_today:
            self._in_stars_today = False
            # 文本形如 "1,234 stars today"，取开头数字
            m = re.match(r"\s*([\d,]+)", self._text_buf)
            if m:
                self._current["stars_today"] = int(m.group(1).replace(",", ""))
        elif tag == "span" and self._in_lang:
            self._in_lang = False
            lang = " ".join(self._text_buf.split()).strip()
            if lang:
                self._current["language"] = lang
        elif tag == "article" and self._in_article:
            self._in_article = False
            if self._current.get("full_name"):
                self.repos.append(self._current)
            self._current = {}

    def handle_data(self, data):
        if (self._in_h2 or self._in_desc or self._in_stars_total
                or self._in_stars_today or self._in_lang):
            self._text_buf += data


def fetch_readme(full_name: str) -> str:
    """抓取仓库 README 正文（默认分支），供摘要阶段做全文素材。失败返回空串。"""
    for fname in README_VARIANTS:
        url = f"https://raw.githubusercontent.com/{full_name}/HEAD/{fname}"
        req = urllib.request.Request(url, headers={"User-Agent": "DevFocus/1.0"})
        try:
            with urllib.request.urlopen(req, timeout=10) as resp:
                text = resp.read().decode("utf-8", errors="replace")
                if text.strip():
                    return text[:README_MAX_CHARS]
        except Exception:
            continue
    return ""


def attach_readmes(repos: list[dict]) -> list[dict]:
    """并发抓取每个 repo 的 README，挂到条目 readme 字段。"""
    if not repos:
        return repos

    def _one(r: dict) -> dict:
        r["readme"] = fetch_readme(r["full_name"])
        return r

    with ThreadPoolExecutor(max_workers=8) as ex:
        results = list(ex.map(_one, repos))
    got = sum(1 for r in results if r.get("readme"))
    print(f"[GH] README fetched: {got}/{len(results)}")
    return results


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
            "language": r.get("language", ""),
            "stars_today": r.get("stars_today", 0),
            "stars_total": r.get("stars_total", 0),
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
            # 兜底拿不到 "stars today"：置 0 而不是用总 star 充数——
            # 总 star 量级与真实日增不可比，会污染跨源排序（此前注释承认
            # 该问题但仍写入）。0 分使兜底条目排在同源末尾，行为可预期。
            "stars_today": 0,
            "stars_total": item.get("stargazers_count", 0),
            "source": "github_trending",
        })
    print(f"[GH] API fallback returned {len(repos)} repos for {period}"
          f"（stars_today 置 0，无日增数据）", file=sys.stderr)
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

        # README 全文（摘要阶段的输入素材，缺 README 的仓库降级用 description）
        if repos:
            repos = attach_readmes(repos)

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
