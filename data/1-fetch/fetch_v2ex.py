"""Fetch hot topics from V2EX (developer forum) via RSS."""
import json
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path

OUT = Path(__file__).parent.parent / "2-raw" / "v2ex.json"
RSS = "https://www.v2ex.com/index.xml"

HEADERS = {"User-Agent": "DevFocus/1.0"}

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
        items.append({
            "id": str(i),
            "title": title,
            "url": link,
            "source": "v2ex",
            "score": 0,
            "time": entry.findtext("pubDate", ""),
            "tags": [],
        })
    
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(items, ensure_ascii=False, indent=2))
    print(f"[V2EX] {len(items)} topics -> {OUT}")

if __name__ == "__main__":
    fetch()
