#!/usr/bin/env python3
from __future__ import annotations

"""Fetch Zhihu (知乎) tech-only items via tophub.today.

Fetches the general Zhihu hot list and filters to tech/science/developer
topics using keyword matching. Non-tech items are discarded.
"""

import json
import re
import sys
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

TOPHUB_URL = "https://tophub.today/n/mproPpoq6O"
MAX_FETCH = 50  # fetch more, filter down
TOP_N = 10
HEADERS = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"}

# Tech/science/developer keywords — title must match at least one
TECH_KEYWORDS = [
    # AI & LLM
    "AI", "人工智能", "大模型", "LLM", "ChatGPT", "GPT", "Claude", "Gemini",
    "豆包", "DeepSeek", "通义", "文心", "Copilot", "AIGC", "AGI",
    "机器学习", "深度学习", "神经网络", "算法", "训练", "推理",
    # Developer & CS
    "编程", "程序员", "代码", "开发", "工程师", "架构", "开源",
    "GitHub", "Python", "Java", "JavaScript", "Rust", "Go", "TypeScript",
    "前端", "后端", "全栈", "运维", "DevOps", "SRE",
    "API", "数据库", "Linux", "Git", "Docker", "Kubernetes",
    # Hardware & Chips
    "芯片", "半导体", "GPU", "CPU", "NPU", "算力", "光刻",
    "英伟达", "NVIDIA", "AMD", "Intel", "高通", "联发科",
    # Big Tech
    "苹果", "Apple", "谷歌", "Google", "微软", "Microsoft",
    "OpenAI", "Meta", "字节", "腾讯", "阿里", "百度", "华为",
    "特斯拉", "SpaceX", "星舰", "火箭",
    # Digital & Devices
    "手机", "iPhone", "安卓", "Android", "iOS", "鸿蒙",
    "芯片", "显卡", "处理器", "服务器", "云计算",
    # Science
    "量子", "核聚变", "航天", "卫星", "火箭", "科学", "论文",
    "基因", "生物", "物理", "化学", "数学",
    # Industry
    "自动驾驶", "机器人", "无人机", "新能源", "电池",
    "5G", "6G", "WiFi", "区块链", "Web3",
]


def is_tech(title: str) -> bool:
    """Check if a title is tech/science related."""
    title_lower = title.lower()
    return any(kw.lower() in title_lower for kw in TECH_KEYWORDS)


def fetch_hot_list() -> list[dict]:
    """Fetch Zhihu hot list from tophub.today, filtered to tech only."""
    req = urllib.request.Request(TOPHUB_URL, headers=HEADERS)
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            html = resp.read().decode("utf-8")
    except Exception as e:
        print(f"[Zhihu] Fetch error: {e}", file=sys.stderr)
        return []

    links = re.findall(
        r'<a[^>]*href="(https://www\.zhihu\.com/question/\d+)"[^>]*target="_blank"[^>]*>([^<]+)</a>',
        html,
    )

    items = []
    seen: set[str] = set()
    for href, title in links[:MAX_FETCH]:
        title = title.strip()
        if not title or len(title) < 5:
            continue
        if not is_tech(title):
            continue
        qid = re.search(r"/question/(\d+)", href)
        qid_str = qid.group(1) if qid else str(hash(title))
        if qid_str in seen:
            continue
        seen.add(qid_str)
        items.append({
            "id": f"zhihu-{qid_str}",
            "title": title,
            "url": href,
            "description": "",
            "source": "zhihu",
            "score": 0,
            "comments": 0,
            "author": "",
            "time": datetime.now(timezone.utc).isoformat(),
            "tags": ["zhihu"],
        })
        if len(items) >= TOP_N:
            break

    return items


def main():
    output_dir = Path(__file__).resolve().parent.parent / "2-raw"
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / "zhihu_daily.json"

    print("[Zhihu] Fetching hot list (tech filter)...")
    items = fetch_hot_list()
    print(f"[Zhihu] Got {len(items)} tech items")

    result = {
        "fetched_at": datetime.now(timezone.utc).isoformat(),
        "source": "zhihu",
        "count": len(items),
        "items": items,
    }
    output_path.write_text(json.dumps(result, indent=2, ensure_ascii=False))
    print(f"[Zhihu] Saved to {output_path.name}")


if __name__ == "__main__":
    main()
