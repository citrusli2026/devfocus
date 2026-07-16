"""Fetch hot topics from V2EX (developer forum) via RSS."""
import hashlib
import json
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path

OUT = Path(__file__).parent.parent / "2-raw" / "v2ex.json"
RSS = "https://www.v2ex.com/index.xml"

HEADERS = {"User-Agent": "DevFocus/1.0"}

def _stable_id(title: str, link: str) -> str:
    """Generate stable ID from title+link hash."""
    raw = (title + link).encode()
    return hashlib.md5(raw).hexdigest()[:12]

def fetch():
    req = urllib.request.Request(RSS, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=30) as resp:
        xml_data = resp.read().decode()

    root = ET.fromstring(xml_data)
    items = []
    for i, entry in enumerate(root.findall(".//item")[:20]):
        title = entry.findtext("title", "")
        link = entry.findtext("link", "")
        desc = entry.findtext("description", "")
        pub_date = entry.findtext("pubDate", "")
        items.append({
            "id": _stable_id(title, link),
            "title": title,
            "url": link,
            "source": "v2ex",
            "score": 0,
            "time": pub_date,
            "tags": [],
        })

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps({"fetched_at": "", "source": "v2ex", "count": len(items), "items": items},
                              ensure_ascii=False, indent=2))
    print(f"[V2EX] {len(items)} topics -> {OUT}")

if __name__ == "__main__":
    fetch()
