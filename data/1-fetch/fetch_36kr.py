"""Fetch hot articles from 36Kr (tech/startup news)."""
import json
import re
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from _common import html_to_text

OUT = Path(__file__).parent.parent / "2-raw" / "36kr.json"
API = "https://gateway.36kr.com/api/mis/nav/home/nav/rank/hot"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)",
    "Content-Type": "application/json",
}

PAGE_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)",
    "Accept": "text/html",
    "Referer": "https://36kr.com/",
}
CONTENT_MAX_CHARS = 2000


def _extract_initial_state_text(html: str) -> str:
    """36kr 是 CSR：正文在 window.initialState 的 articleDetail.content 里。"""
    try:
        m = re.search(r'window\.initialState\s*=\s*(\{.*?\});?\s*(?:</script>|$)', html, re.S)
        if not m:
            return ""
        state = json.loads(m.group(1))
        # 常见路径：articleDetail.content / articleDetail.widgetContent
        detail = (state.get("articleDetail") or {}).get("articleDetail") or state.get("articleDetail") or {}
        for key in ("content", "widgetContent"):
            val = detail.get(key)
            if isinstance(val, str) and val.strip():
                return html_to_text(val, max_chars=CONTENT_MAX_CHARS)
    except Exception:
        pass
    return ""


def fetch_article_content(item_id: str) -> str:
    """抓取文章正文（尽力而为）：CSR 页面解析 initialState；失败返回空串降级。"""
    url = f"https://36kr.com/p/{item_id}"
    try:
        req = urllib.request.Request(url, headers=PAGE_HEADERS)
        with urllib.request.urlopen(req, timeout=15) as resp:
            html = resp.read().decode("utf-8", errors="replace")
        # Cloudflare 验证页（无真实标题）→ 视为失败
        if "<title>" not in html or "Checking your browser" in html:
            return ""
        text = _extract_initial_state_text(html)
        if not text:
            text = html_to_text(html, max_chars=CONTENT_MAX_CHARS)
        return text
    except Exception:
        return ""


def fetch():
    payload = json.dumps({"partner_id": "wap", "param": {"siteId": 1, "platformId": 2}}).encode()
    req = urllib.request.Request(API, data=payload, headers=HEADERS, method="POST")
    with urllib.request.urlopen(req, timeout=30) as resp:
        data = json.loads(resp.read().decode())
    
    items = []
    for item in (data.get("data", {}).get("hotRankList", []) or [])[:20]:
        template = item.get("templateMaterial", {})
        items.append({
            "id": str(item.get("itemId", "")),
            "title": template.get("widgetTitle", ""),
            "url": f"https://36kr.com/p/{item.get('itemId', '')}",
            "source": "36kr",
            "score": template.get("statRead", 0),
            "time": template.get("publishTime", ""),
            "tags": [],
        })

    # 并发抓正文（摘要阶段的输入素材，失败条目 content 留空降级）
    if items:
        with ThreadPoolExecutor(max_workers=8) as ex:
            contents = list(ex.map(lambda it: fetch_article_content(it["id"]), items))
        for it, c in zip(items, contents):
            it["content"] = c
        got = sum(1 for c in contents if c)
        print(f"[36Kr] content fetched: {got}/{len(items)}")

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(items, ensure_ascii=False, indent=2))
    print(f"[36Kr] {len(items)} articles -> {OUT}")

if __name__ == "__main__":
    fetch()
