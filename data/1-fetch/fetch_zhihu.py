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

# Strict tech/developer keywords — title must match at least one
# Removed overly broad terms: 科学, 新能源, 数学, 化学, 生物, 物理
TECH_KEYWORDS = [
    # AI & LLM (core focus)
    "AI", "人工智能", "大模型", "LLM", "ChatGPT", "GPT", "Claude", "Gemini",
    "豆包", "DeepSeek", "通义", "文心", "Copilot", "AIGC", "AGI",
    "机器学习", "深度学习", "神经网络", "算法",
    # Developer & CS
    "编程", "程序员", "代码", "开发", "工程师", "架构", "开源",
    "GitHub", "Python", "Java", "JavaScript", "Rust", "Go", "TypeScript",
    "前端", "后端", "全栈", "运维", "DevOps",
    "API", "数据库", "Linux", "Git", "Docker", "Kubernetes",
    # Hardware & Chips
    "芯片", "半导体", "GPU", "CPU", "算力", "光刻",
    "英伟达", "NVIDIA", "AMD", "Intel", "高通",
    # Big Tech
    "苹果", "Apple", "谷歌", "Google", "微软", "Microsoft",
    "OpenAI", "Meta", "字节", "腾讯", "阿里", "百度", "华为",
    "特斯拉", "SpaceX", "星舰",
    # Digital & Devices
    "iPhone", "安卓", "Android", "iOS", "鸿蒙",
    "显卡", "处理器", "服务器", "云计算",
    # Automation & Robotics
    "自动驾驶", "机器人", "无人机",
    "5G", "6G", "区块链",
]

# Negative keywords — exclude even if tech keyword matched
EXCLUDE_KEYWORDS = [
    "汽车", "燃油车", "新能源车", "车主", "换车",
    "厄尔尼诺", "气候", "天气",
    "高考", "考研", "选专业",
    "减肥", "健身", "养生",
    "做饭", "煮饭", "菜谱",
    "选专业", "专业", "职业", "职业规划",
    "羡慕", "恐惧", "哲学", "意识", "灵魂",
]


def is_tech(title: str) -> bool:
    """Check if a title is tech/science related."""
    title_lower = title.lower()
    # Check exclusions first
    if any(ex.lower() in title_lower for ex in EXCLUDE_KEYWORDS):
        return False
    return any(kw.lower() in title_lower for kw in TECH_KEYWORDS)


def parse_heat(text: str) -> int:
    """Parse tophub heat text like '1235 万热度' / '697 万热度' to a raw number.

    Returns 0 when unparseable (caller falls back to rank-based score).
    """
    m = re.search(r"([\d.]+)", text)
    if not m:
        return 0
    val = float(m.group(1))
    if "万" in text:
        val *= 10000
    return int(val)


def fetch_hot_list() -> list[dict]:
    """Fetch Zhihu hot list from tophub.today, filtered to tech only."""
    req = urllib.request.Request(TOPHUB_URL, headers=HEADERS)
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            html = resp.read().decode("utf-8")
    except Exception as e:
        print(f"[Zhihu] Fetch error: {e}", file=sys.stderr)
        return []

    # Each list row is: title anchor followed by '<div class="item-desc">N 万热度</div>'.
    # Capture both in one pass so heat stays aligned with its title.
    rows = re.findall(
        r'<a[^>]*href="(https://www\.zhihu\.com/question/\d+)"[^>]*target="_blank"[^>]*>([^<]+)</a></div>'
        r'\s*<div class="item-desc">([^<]*)</div>',
        html,
        re.S,
    )

    items = []
    seen: set[str] = set()
    for rank, (href, title, heat_text) in enumerate(rows[:MAX_FETCH]):
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
        heat = parse_heat(heat_text)
        # 热度解析失败（页面结构变化）时退化为排名分：第 1 名 50 分，逐名 -5
        score = heat if heat > 0 else max(50 - len(items) * 5, 5)
        items.append({
            "id": f"zhihu-{qid_str}",
            "title": title,
            "url": href,
            "description": "",
            "source": "zhihu",
            "score": score,
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
