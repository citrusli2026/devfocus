"""Fetch hot articles from 36Kr (tech/startup news)."""
from __future__ import annotations

import json
import sys
import urllib.request
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from _common import fetch_with_retry, html_to_text

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


def _extract_initial_state_json(html: str) -> dict | None:
    """定位 window.initialState = {...} 并用括号配对截取完整 JSON 对象。

    不能用非贪婪正则：字符串值内出现 '};' 时会提前截断（实测导致解析失败），
    这里做带字符串/转义感知的括号配对扫描。
    """
    idx = html.find("window.initialState")
    if idx < 0:
        return None
    brace = html.find("{", idx)
    if brace < 0:
        return None
    depth = 0
    in_str = False
    esc = False
    i = brace
    n = len(html)
    while i < n:
        c = html[i]
        if in_str:
            if esc:
                esc = False
            elif c == "\\":
                esc = True
            elif c == '"':
                in_str = False
        else:
            if c == '"':
                in_str = True
            elif c == "{":
                depth += 1
            elif c == "}":
                depth -= 1
                if depth == 0:
                    return json.loads(html[brace:i + 1])
        i += 1
    return None


def _extract_initial_state_text(html: str) -> str:
    """36kr 是 CSR：正文在 window.initialState 的 articleDetail.content 里。"""
    try:
        state = _extract_initial_state_json(html)
        if state is None:
            return ""
        # 常见路径：articleDetail.content / articleDetail.widgetContent
        detail = (state.get("articleDetail") or {}).get("articleDetail") or state.get("articleDetail") or {}
        for key in ("content", "widgetContent"):
            val = detail.get(key)
            if isinstance(val, str) and val.strip():
                return html_to_text(val, max_chars=CONTENT_MAX_CHARS)
    except Exception:
        pass
    return ""


def fetch_article_content(item_id: str) -> tuple[str, str]:
    """抓取文章正文，返回 (正文, 结果类别)。

    正文为空时类别说明失败原因（cloudflare / no-title / empty / error:...），
    供 main 汇总告警——避免"全挂但无声"的静默降级。
    """
    url = f"https://36kr.com/p/{item_id}"
    try:
        req = urllib.request.Request(url, headers=PAGE_HEADERS)
        with urllib.request.urlopen(req, timeout=15) as resp:
            html = resp.read().decode("utf-8", errors="replace")
        # Cloudflare 验证页 → 视为失败
        if "Checking your browser" in html or "cf-challenge" in html:
            return "", "cloudflare"
        if "<title>" not in html:
            return "", "no-title"
        text = _extract_initial_state_text(html)
        if text:
            return text, "ok"
        text = html_to_text(html, max_chars=CONTENT_MAX_CHARS)
        if text:
            return text, "fulltext"
        return "", "empty"
    except Exception as e:
        return "", f"error:{type(e).__name__}"


def fetch():
    payload = json.dumps({"partner_id": "wap", "param": {"siteId": 1, "platformId": 2}}).encode()
    _, body = fetch_with_retry(API, timeout=30, method="POST", data=payload, headers=HEADERS)
    data = json.loads(body.decode())
    
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
        with ThreadPoolExecutor(max_workers=4) as ex:
            results = list(ex.map(lambda it: fetch_article_content(it["id"]), items))
        reasons = Counter(r for _, r in results)
        for it, (c, _) in zip(items, results):
            it["content"] = c
        got = sum(1 for c, _ in results if c)
        print(f"[36Kr] content fetched: {got}/{len(items)} ({dict(reasons)})")
        if got == 0:
            print("[36Kr] WARN: 全部正文抓取失败，请检查 36kr 页面结构或反爬变化",
                  file=sys.stderr)

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(items, ensure_ascii=False, indent=2))
    print(f"[36Kr] {len(items)} articles -> {OUT}")

if __name__ == "__main__":
    fetch()
