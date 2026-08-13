#!/usr/bin/env python3
"""Build topic trends from historical snapshots → trends.json.

Output schema (docs/designs/2026-06-21-temporal-design.md):
  {
    "generated_at": ISO datetime,
    "period": "YYYY-MM-DD ~ YYYY-MM-DD",
    "dates": [...],                      # 周期内全部日期（热力图横轴）
    "topics": [
      {"keyword", "count", "trend",      # trend: rising|falling|stable|new
       "heat_by_date", "sample_titles", "sources"}
    ],
    "source_activity": {source: {date: count}}
  }

话题聚类：标准库实现（项目约定最小依赖，不引入 jieba）
  - 中文：按连续汉字段切 2-4 字滑窗，过滤虚字/停用短语
  - 英文：停用词+泛用词过滤后的 unigram，相邻内容词 bigram
  - 内置技术词表兜底（ASCII 整词匹配，CJK 子串匹配）
  - 同一关键词命中 ≥2 条 → 归为一个话题
"""

import json
import re
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

DATA = Path(__file__).resolve().parent.parent
HISTORY = DATA / "5-history"
OUTPUT = DATA / "4-final" / "trends.json"

MAX_TOPICS = 35
MIN_HITS = 2  # 关键词至少命中条目数才成为话题

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
    "our", "his", "her", "he", "she", "my", "me", "i", "via", "vs",
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
    "guide", "tutorial", "intro", "introduction", "week", "month", "hn",
    "now", "model", "chat", "control", "one",
}

# 中文滑窗碎词过滤规则在 _shared.py（enrich.py 共用，勿分叉）
from _shared import CN_FUNC_CHARS, CN_JUNK_SUBSTR, CN_STOP_PHRASES

# Known tech keywords to boost.
# ASCII 条目按整词匹配（避免 "ai" 命中 "said"、"go" 命中 "google"），
# CJK 条目按子串匹配。
TECH_KEYWORDS = {
    "ai", "llm", "gpt", "claude", "gemini", "deepseek", "qwen", "llama",
    "python", "rust", "go", "golang", "javascript", "typescript", "react",
    "vue", "docker", "kubernetes", "linux", "git", "github", "api", "sdk",
    "machine learning", "deep learning", "neural", "transformer", "mcp",
    "openai", "anthropic", "google", "meta", "microsoft", "apple", "nvidia",
    "agent", "agents", "rag", "embedding", "fine-tune", "inference",
    "training", "benchmark", "startup", "cursor", "copilot", "devin",
    "芯片", "大模型", "开源", "编程", "算法", "数据库", "框架", "智能体",
    "前端", "后端", "全栈", "微服务", "云原生", "容器", "部署", "云计算",
    "性能", "优化", "安全", "隐私", "区块链", "融资", "收购", "自动驾驶",
    "人工智能", "机器人", "量子", "半导体", "国产", "模型",
}


def _is_cjk(s: str) -> bool:
    return any("\u4e00" <= c <= "\u9fff" for c in s)


# 预编译 ASCII 技术词的整词匹配
_TECH_PATTERNS = [
    (kw, None if _is_cjk(kw) else re.compile(
        r"(?<![a-z0-9])" + re.escape(kw) + r"(?![a-z0-9])"))
    for kw in TECH_KEYWORDS
]

_WORD_RE = re.compile(r"[a-zA-Z]{2,}")
_CJK_RUN_RE = re.compile(r"[\u4e00-\u9fff]+")


def extract_keywords(title: str) -> set[str]:
    """Extract meaningful keywords from a mixed CN/EN title."""
    keywords: set[str] = set()
    title_lower = title.lower()

    # 1) 内置技术词表
    for kw, pattern in _TECH_PATTERNS:
        if pattern is None:  # CJK 子串匹配
            if kw in title:
                keywords.add(kw)
        elif pattern.search(title_lower):  # ASCII 整词匹配
            keywords.add(kw)

    # 2) 英文 unigram（≥3 字母，非停用词/泛用词）
    words = [w.lower() for w in _WORD_RE.findall(title)]
    for wl in words:
        if len(wl) >= 3 and wl not in STOP and wl not in GENERIC:
            keywords.add(wl)

    # 3) 英文 bigram（相邻内容词；两个词都是泛用词则跳过）
    for a, b in zip(words, words[1:]):
        if a in STOP or b in STOP:
            continue
        if a in GENERIC and b in GENERIC:
            continue
        keywords.add(f"{a} {b}")

    # 4) 中文：连续汉字段内 2-4 字滑窗，过滤虚字与停用短语
    for run in _CJK_RUN_RE.findall(title):
        if len(run) == 1:
            continue
        for n in (2, 3, 4):
            if len(run) < n:
                continue
            for i in range(len(run) - n + 1):
                gram = run[i:i + n]
                if gram in CN_STOP_PHRASES:
                    continue
                if any(j in gram for j in CN_JUNK_SUBSTR):
                    continue
                if any(c in CN_FUNC_CHARS for c in gram):
                    continue
                keywords.add(gram)

    return keywords


def load_snapshots() -> dict[str, list[dict]]:
    """Load all snapshots: date_str → items."""
    snapshots = {}
    for f in sorted(HISTORY.glob("*.json")):
        try:
            data = json.loads(f.read_text())
        except (ValueError, json.JSONDecodeError):
            continue
        items = data.get("items", [])
        if items:
            snapshots[f.stem] = items
    return snapshots


def build_keyword_heat(snapshots: dict[str, list[dict]]):
    """Aggregate per-keyword stats.

    Returns (kw_heat, kw_hits, kw_sources, kw_samples):
      kw_heat:    keyword → {date: heat}，热度 = 命中条目 score 之和（按源归一化到 0-100，避免 HN 一家独大）
      kw_hits:    keyword → {(date, id)} 命中集合
      kw_sources: keyword → {source}
      kw_samples: keyword → [(norm_score, title)] 按热度取前 3
    """
    # First pass: find max score per source across all dates
    source_max: dict[str, float] = defaultdict(float)
    for items in snapshots.values():
        for item in items:
            src = item.get("source", "unknown")
            score = max(item.get("score", 1) or 1, 1)
            source_max[src] = max(source_max[src], score)

    # Second pass: normalize scores per source (0-100 scale)
    kw_heat: dict[str, dict[str, float]] = defaultdict(lambda: defaultdict(float))
    kw_hits: dict[str, set] = defaultdict(set)
    kw_sources: dict[str, set] = defaultdict(set)
    kw_samples: dict[str, list] = defaultdict(list)
    for date_str, items in snapshots.items():
        for item in items:
            title = item.get("title", "")
            if not title:
                continue
            src = item.get("source", "unknown")
            raw_score = max(item.get("score", 1) or 1, 1)
            norm_score = (raw_score / source_max[src]) * 100 if source_max[src] > 0 else 1
            for kw in extract_keywords(title):
                kw_heat[kw][date_str] += norm_score
                kw_hits[kw].add((date_str, item.get("id", title)))
                kw_sources[kw].add(src)
                samples = kw_samples[kw]
                samples.append((norm_score, title))
                samples.sort(key=lambda x: x[0], reverse=True)
                del samples[3:]

    return kw_heat, kw_hits, kw_sources, kw_samples


def classify_trend(heat_by_date: dict[str, float], dates: list[str]) -> str:
    """Classify trend direction（设计文档口径）:
    new:    最近 2 天首次出现
    rising: 近 3 天热度均值 > 前 3 天均值 × 1.5
    falling: 近 3 天热度均值 < 前 3 天均值 ÷ 1.5
    stable: 其他
    """
    if len(dates) < 2:
        return "stable"
    active = [d for d in dates if heat_by_date.get(d, 0) > 0]
    if not active:
        return "stable"

    if active[0] in dates[-2:]:
        return "new"

    recent, earlier = dates[-3:], dates[-6:-3]
    if not earlier:
        return "stable"
    recent_avg = sum(heat_by_date.get(d, 0) for d in recent) / len(recent)
    earlier_avg = sum(heat_by_date.get(d, 0) for d in earlier) / len(earlier)
    if earlier_avg == 0:
        return "rising" if recent_avg > 0 else "stable"
    if recent_avg > earlier_avg * 1.5:
        return "rising"
    if recent_avg < earlier_avg / 1.5:
        return "falling"
    return "stable"


def dedup_contained(keywords: list[str], counts: dict[str, int]) -> list[str]:
    """去掉被更长话题词覆盖的纯中文碎片词。

    规则：若存在更长关键词 K 使得 kw ⊂ K 且 count(K) ≥ 0.8 × count(kw)，
    说明 kw 的命中基本都来自 K（如 "器人" 之于 "机器人"），丢弃 kw。
    仅对纯中文词生效，避免误伤 "ai agent" 之于 "ai" 这类英文组合。
    """
    cjk = [k for k in keywords
           if _is_cjk(k) and not re.search(r"[a-z0-9]", k)]
    dropped = set()
    for kw in cjk:
        for longer in cjk:
            if kw != longer and kw in longer and counts[longer] >= counts[kw] * 0.8:
                dropped.add(kw)
                break
    return [k for k in keywords if k not in dropped]


def main():
    snapshots = load_snapshots()
    if not snapshots:
        print("[Trends] 无历史快照")
        return

    dates = sorted(snapshots.keys())
    print(f"[Trends] {len(dates)} 天数据: {dates[0]} ~ {dates[-1]}")

    kw_heat, kw_hits, kw_sources, kw_samples = build_keyword_heat(snapshots)

    # 聚类规则：同一关键词命中 ≥ MIN_HITS 条 → 话题
    counts = {kw: len(hits) for kw, hits in kw_hits.items()}
    candidates = [kw for kw, c in counts.items() if c >= MIN_HITS and len(kw) >= 2]
    candidates = dedup_contained(candidates, counts)

    topics = []
    for kw in candidates:
        heat_map = kw_heat[kw]
        total_heat = sum(heat_map.values())
        full_heat = {d: int(round(heat_map.get(d, 0))) for d in dates}
        topics.append({
            "keyword": kw,
            "count": counts[kw],
            "trend": classify_trend(heat_map, dates),
            "heat_by_date": full_heat,
            "sample_titles": [t for _, t in kw_samples.get(kw, [])],
            "sources": sorted(kw_sources.get(kw, set())),
            "_total_heat": total_heat,
        })

    # 按总热度排序取 top N
    topics.sort(key=lambda t: t["_total_heat"], reverse=True)
    topics = topics[:MAX_TOPICS]
    for t in topics:
        del t["_total_heat"]

    # Source activity
    source_activity: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
    for date_str, items in snapshots.items():
        for item in items:
            source_activity[item.get("source", "unknown")][date_str] += 1
    source_activity_flat = {
        src: {d: act.get(d, 0) for d in dates}
        for src, act in source_activity.items()
    }

    result = {
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "period": f"{dates[0]} ~ {dates[-1]}",
        "dates": dates,
        "topics": topics,
        "source_activity": source_activity_flat,
    }

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(result, ensure_ascii=False, indent=2))
    by_trend = defaultdict(int)
    for t in topics:
        by_trend[t["trend"]] += 1
    trend_str = ", ".join(f"{k}:{v}" for k, v in sorted(by_trend.items()))
    print(f"[Trends] {len(topics)} 话题 ({trend_str}) → {OUTPUT}")


if __name__ == "__main__":
    main()
