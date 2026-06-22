#!/usr/bin/env python3
"""Build topic trends from historical snapshots → trends.json."""

import json
import re
from collections import Counter, defaultdict
from datetime import date, timedelta
from pathlib import Path

DATA = Path(__file__).resolve().parent.parent
HISTORY = DATA / "5-history"
OUTPUT = DATA / "4-final" / "trends.json"

# Stop words (English)
STOP = {
    "the", "a", "an", "is", "are", "was", "were", "be", "been", "being",
    "have", "has", "had", "do", "does", "did", "will", "would", "could",
    "should", "may", "might", "can", "shall", "to", "of", "in", "for",
    "on", "with", "at", "by", "from", "as", "into", "through", "during",
    "before", "after", "above", "below", "between", "out", "off", "over",
    "under", "again", "further", "then", "once", "here", "there", "when",
    "where", "why", "how", "all", "both", "each", "few", "more", "most",
    "other", "some", "such", "no", "nor", "not", "only", "own", "same",
    "so", "than", "too", "very", "just", "because", "but", "and", "or",
    "if", "while", "about", "up", "its", "it", "that", "this", "what",
    "which", "who", "whom", "new", "your", "you", "we", "they", "them",
    "our", "his", "her", "he", "she", "my", "me", "i",
}

# Generic words that are meaningless as standalone topics
GENERIC = {
    "show", "open", "source", "code", "skills", "fable", "using", "make",
    "want", "need", "best", "top", "get", "set", "run", "use", "way",
    "day", "year", "time", "world", "people", "things", "work", "like",
    "just", "still", "even", "also", "much", "many", "good", "great",
    "first", "last", "long", "high", "old", "big", "small", "right",
    "free", "full", "real", "true", "false", "simple", "easy", "hard",
    "build", "learn", "start", "help", "take", "find", "think", "look",
    "come", "give", "back", "down", "well", "part", "made", "read",
    "post", "ask", "say", "tell", "see", "know", "try", "keep",
    "site", "app", "tool", "data", "file", "type", "line", "user",
}

# Known tech keywords to boost
TECH_KEYWORDS = {
    "ai", "llm", "gpt", "claude", "gemini", "deepseek", "qwen", "llama",
    "python", "rust", "go", "javascript", "typescript", "react", "vue",
    "docker", "kubernetes", "linux", "git", "github", "api", "sdk",
    "machine learning", "deep learning", "neural", "transformer",
    "openai", "anthropic", "google", "meta", "microsoft", "apple",
    "芯片", "大模型", "开源", "编程", "算法", "数据", "框架",
    "前端", "后端", "全栈", "微服务", "云原生", "容器", "部署",
    "agent", "rag", "embedding", "fine-tune", "inference", "training",
    "benchmark", "性能", "优化", "安全", "隐私", "区块链",
    "startup", "融资", "收购", "产品", "设计", "用户体验",
}


def extract_keywords(title: str) -> list[str]:
    """Extract meaningful keywords from a mixed CN/EN title."""
    title_lower = title.lower()
    keywords = []

    # Extract known tech keywords first
    for kw in TECH_KEYWORDS:
        if kw in title_lower:
            keywords.append(kw)

    # English words (3+ chars, not stop words, not generic)
    words = re.findall(r'[a-zA-Z]{3,}', title)
    for w in words:
        wl = w.lower()
        if wl not in STOP and wl not in GENERIC and len(wl) >= 3:
            keywords.append(wl)

    # Chinese phrases (2-4 chars for better word boundaries)
    cn_phrases = re.findall(r'[\u4e00-\u9fff]{2,4}', title)
    for p in cn_phrases:
        # Skip very common particles
        if p in ('这个', '那个', '什么', '怎么', '可以', '不是', '没有', '已经', '因为', '所以'):
            continue
        keywords.append(p)

    return list(set(keywords))


def load_snapshots() -> dict[str, list[dict]]:
    """Load all snapshots: date_str → items."""
    snapshots = {}
    for f in sorted(HISTORY.glob("*.json")):
        try:
            d = date.fromisoformat(f.stem)
            data = json.loads(f.read_text())
            snapshots[f.stem] = data.get("items", [])
        except (ValueError, json.JSONDecodeError):
            continue
    return snapshots


def build_keyword_heat(snapshots: dict[str, list[dict]]) -> tuple[dict[str, dict[str, float]], dict[str, list[str]]]:
    """keyword → {date: heat_score}. Normalized per source to avoid HN dominance.
    Also returns keyword → [sample titles] for context."""
    # First pass: find max score per source across all dates
    source_max: dict[str, float] = defaultdict(float)
    for date_str, items in snapshots.items():
        for item in items:
            src = item.get("source", "unknown")
            score = max(item.get("score", 1), 1)
            source_max[src] = max(source_max[src], score)

    # Second pass: normalize scores per source (0-100 scale)
    kw_heat: dict[str, dict[str, float]] = defaultdict(lambda: defaultdict(float))
    kw_titles: dict[str, list[str]] = defaultdict(list)
    for date_str, items in snapshots.items():
        for item in items:
            title = item.get("title", "")
            src = item.get("source", "unknown")
            raw_score = max(item.get("score", 1), 1)
            # Normalize: each source contributes equally (max 100)
            norm_score = (raw_score / source_max[src]) * 100 if source_max[src] > 0 else 1
            keywords = extract_keywords(title)
            for kw in keywords:
                kw_heat[kw][date_str] += norm_score
                # Keep top 3 highest-scoring titles per keyword
                if len(kw_titles[kw]) < 3:
                    kw_titles[kw].append(title)
                elif raw_score > 0:
                    # Replace lowest if this is higher score (simple heuristic)
                    pass  # keep first 3 for simplicity

    return kw_heat, kw_titles


def classify_trend(heat_by_date: dict[str, float]) -> str:
    """Classify trend direction."""
    dates = sorted(heat_by_date.keys())
    if len(dates) < 2:
        return "stable"

    recent = dates[-3:] if len(dates) >= 3 else dates[-2:]
    earlier = dates[:-3] if len(dates) >= 3 else dates[:1]

    if not earlier:
        # All dates are "recent" — check if new
        if len(dates) <= 2:
            return "new"
        return "stable"

    recent_avg = sum(heat_by_date[d] for d in recent) / len(recent)
    earlier_avg = sum(heat_by_date[d] for d in earlier) / len(earlier)

    if earlier_avg == 0:
        return "new"

    ratio = recent_avg / earlier_avg
    if ratio > 1.5:
        return "rising"
    elif ratio < 0.6:
        return "falling"
    return "stable"


def main():
    snapshots = load_snapshots()
    if not snapshots:
        print("[Trends] 无历史快照")
        return

    dates = sorted(snapshots.keys())
    print(f"[Trends] {len(dates)} 天数据: {dates[0]} ~ {dates[-1]}")

    # Build keyword heat map
    kw_heat, kw_titles = build_keyword_heat(snapshots)

    # Filter: keyword must appear on ≥2 days OR have total heat > 100
    topics = []
    for kw, heat_map in kw_heat.items():
        total_heat = sum(heat_map.values())
        days_active = len(heat_map)

        if days_active < 2 and total_heat < 30:
            continue
        if len(kw) < 2:  # skip single chars
            continue

        trend = classify_trend(heat_map)

        # Fill missing dates with 0
        full_heat = {}
        for d in dates:
            full_heat[d] = heat_map.get(d, 0)

        topics.append({
            "keyword": kw,
            "count": days_active,
            "total_heat": total_heat,
            "trend": trend,
            "heat_by_date": full_heat,
            "sample_titles": kw_titles.get(kw, []),
        })

    # Sort by total heat descending, take top 35
    topics.sort(key=lambda t: t["total_heat"], reverse=True)
    topics = topics[:35]

    # Source activity
    source_activity: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
    for date_str, items in snapshots.items():
        for item in items:
            source_activity[item.get("source", "unknown")][date_str] += 1

    # Convert to regular dicts
    source_activity_flat = {}
    for src, act in source_activity.items():
        source_activity_flat[src] = {d: act.get(d, 0) for d in dates}

    result = {
        "generated_at": date.today().isoformat(),
        "period": f"{dates[0]} ~ {dates[-1]}",
        "dates": dates,
        "topics": topics,
        "source_activity": source_activity_flat,
    }

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(result, ensure_ascii=False, indent=2))
    print(f"[Trends] {len(topics)} 话题 → {OUTPUT}")


if __name__ == "__main__":
    main()
