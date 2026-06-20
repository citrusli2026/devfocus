"""Fetch hot articles from 36Kr (tech/startup news)."""
import json
import urllib.request
from pathlib import Path

OUT = Path(__file__).parent.parent / "2-raw" / "36kr.json"
API = "https://gateway.36kr.com/api/mis/nav/home/nav/rank/hot"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)",
    "Content-Type": "application/json",
}

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
    
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(items, ensure_ascii=False, indent=2))
    print(f"[36Kr] {len(items)} articles -> {OUT}")

if __name__ == "__main__":
    fetch()
