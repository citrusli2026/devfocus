"""Fetch hot articles from InfoQ China (developer/engineering content)."""
import json
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from _common import fetch_with_retry, html_to_text

OUT = Path(__file__).parent.parent / "2-raw" / "infoq.json"
API = "https://www.infoq.cn/public/v1/my/recommond"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)",
    "Content-Type": "application/json",
    "Referer": "https://www.infoq.cn/",
}

PAGE_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)",
    "Accept": "text/html",
    "Referer": "https://www.infoq.cn/",
}
CONTENT_MAX_CHARS = 2000


def fetch_article_content(uuid: str) -> str:
    """抓取文章页正文（ProseMirror 容器，服务端渲染）。失败返回空串。"""
    url = f"https://www.infoq.cn/article/{uuid}"
    try:
        req = urllib.request.Request(url, headers=PAGE_HEADERS)
        with urllib.request.urlopen(req, timeout=15) as resp:
            html = resp.read().decode("utf-8", errors="replace")
        return html_to_text(html, max_chars=CONTENT_MAX_CHARS, target_class="ProseMirror")
    except Exception:
        return ""


def fetch():
    payload = json.dumps({"size": 20}).encode()
    _, body = fetch_with_retry(API, timeout=30, method="POST", data=payload, headers=HEADERS)
    data = json.loads(body.decode())
    
    items = []
    for item in (data.get("data", []) or [])[:20]:
        items.append({
            "id": str(item.get("uuid", "")),
            "title": item.get("article_title", ""),
            "url": f"https://www.infoq.cn/article/{item.get('uuid', '')}",
            "source": "infoq",
            "score": item.get("views", 0),
            "time": item.get("publish_time", ""),
            "tags": [],
        })

    # 并发抓正文（摘要阶段的输入素材，失败条目 content 留空降级）
    if items:
        with ThreadPoolExecutor(max_workers=8) as ex:
            contents = list(ex.map(lambda it: fetch_article_content(it["id"]), items))
        for it, c in zip(items, contents):
            it["content"] = c
        got = sum(1 for c in contents if c)
        print(f"[InfoQ] content fetched: {got}/{len(items)}")

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(items, ensure_ascii=False, indent=2))
    print(f"[InfoQ] {len(items)} articles -> {OUT}")

if __name__ == "__main__":
    fetch()
