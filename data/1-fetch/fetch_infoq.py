"""Fetch hot articles from InfoQ China (developer/engineering content)."""
import json
import urllib.request
from pathlib import Path

OUT = Path(__file__).parent.parent / "2-raw" / "infoq.json"
API = "https://www.infoq.cn/public/v1/my/recommond"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)",
    "Content-Type": "application/json",
    "Referer": "https://www.infoq.cn/",
}

def fetch():
    payload = json.dumps({"size": 20}).encode()
    req = urllib.request.Request(API, data=payload, headers=HEADERS, method="POST")
    with urllib.request.urlopen(req, timeout=30) as resp:
        data = json.loads(resp.read().decode())
    
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
    
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(items, ensure_ascii=False, indent=2))
    print(f"[InfoQ] {len(items)} articles -> {OUT}")

if __name__ == "__main__":
    fetch()
