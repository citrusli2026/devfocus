#!/usr/bin/env python3
"""Enrich feed items with derived metadata: tags, domain, quality score, related items.

Input: 4-final/feed.json, 4-final/summaries.json
Output: enriched 4-final/feed.json (in-place)
"""

from __future__ import annotations

import json
import re
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse

DATA = Path(__file__).resolve().parent.parent
FEED_PATH = DATA / "4-final" / "feed.json"
DIGEST_PATH = DATA / "4-final" / "digest.json"
SUMMARIES_PATH = DATA / "4-final" / "summaries.json"

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

TECH_KEYWORDS = {
    "ai", "llm", "gpt", "claude", "gemini", "deepseek", "qwen", "llama",
    "python", "rust", "go", "golang", "javascript", "typescript", "react", "vue",
    "docker", "kubernetes", "linux", "git", "github", "api", "sdk",
    "machine learning", "deep learning", "neural", "transformer",
    "openai", "anthropic", "google", "meta", "microsoft", "apple",
    "芯片", "大模型", "开源", "编程", "算法", "数据", "框架",
    "前端", "后端", "全栈", "微服务", "云原生", "容器", "部署",
    "agent", "rag", "embedding", "fine-tune", "inference", "training",
    "benchmark", "性能", "优化", "安全", "隐私", "区块链",
    "startup", "融资", "收购", "产品", "设计", "用户体验",
    "cursor", "codex", "copilot", "vibe coding",
}


def extract_domain(url: str) -> str:
    try:
        host = urlparse(url).hostname or ""
        return host.replace("www.", "").lower()
    except Exception:
        return ""


def domain_tag(domain: str) -> str:
    """Map domain to a concise tag."""
    mapping = {
        "github.com": "github",
        "news.ycombinator.com": "hackernews",
        "producthunt.com": "product-hunt",
        "36kr.com": "36kr",
        "juejin.cn": "juejin",
        "zhihu.com": "zhihu",
        "infoq.cn": "infoq",
        "twitter.com": "twitter",
        "x.com": "twitter",
        "arxiv.org": "arxiv",
        "youtube.com": "youtube",
    }
    return mapping.get(domain, domain.split(".")[0] if domain else "")


def extract_keywords(title: str, description: str = "") -> list[str]:
    text = f"{title} {description}".lower()
    keywords = []

    # Known tech keywords
    for kw in TECH_KEYWORDS:
        if kw in text:
            keywords.append(kw)

    # English words
    for w in re.findall(r"[a-zA-Z]{3,}", text):
        wl = w.lower()
        if wl not in STOP and wl not in GENERIC and len(wl) >= 3:
            keywords.append(wl)

    # Chinese phrases
    for p in re.findall(r"[\u4e00-\u9fff]{2,4}", text):
        if p in ("这个", "那个", "什么", "怎么", "可以", "不是", "没有", "已经", "因为", "所以"):
            continue
        keywords.append(p)

    return list(set(keywords))


def parse_time(t):
    try:
        if isinstance(t, (int, float)) and t > 0:
            if t > 1e12:
                t = t / 1000
            return datetime.fromtimestamp(t, tz=timezone.utc)
        s = str(t)
        if s.isdigit():
            n = int(s)
            if n > 1e12:
                n = n / 1000
            return datetime.fromtimestamp(n, tz=timezone.utc)
        dt = datetime.fromisoformat(s.replace("Z", "+00:00"))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt
    except Exception:
        return None


def compute_quality_score(item: dict, has_summary: bool, max_score: float, max_comments: float) -> float:
    """Compute a 0-100 quality score combining engagement, recency and enrichment."""
    score = item.get("score", 0)
    comments = item.get("comments", 0)

    score_norm = (score / max_score * 100) if max_score > 0 else 0
    comments_norm = (comments / max_comments * 100) if max_comments > 0 else 0

    # Recency: items from last 7 days get a boost
    dt = parse_time(item.get("time", ""))
    now = datetime.now(timezone.utc)
    recency = 0.0
    if dt:
        days_old = (now - dt).days
        if days_old <= 1:
            recency = 30
        elif days_old <= 7:
            recency = 15
        elif days_old <= 30:
            recency = 5

    summary_bonus = 10 if has_summary else 0

    # Combine: engagement average + recency + summary bonus
    quality = (score_norm * 0.35 + comments_norm * 0.35 + recency + summary_bonus)
    return min(round(quality, 1), 100)


def build_inverted_index(all_items: list[dict]) -> dict[str, list[dict]]:
    """keyword -> list of items that contain it."""
    index: dict[str, list[dict]] = {}
    for item in all_items:
        kws = set(item.get("tags", [])) | set(extract_keywords(item.get("title", ""), item.get("description", "")))
        for kw in kws:
            index.setdefault(kw, []).append(item)
    return index


def find_related(item: dict, inverted_index: dict[str, list[dict]], item_by_id: dict[str, dict], top_n: int = 5) -> list[str]:
    """Find related items by keyword overlap using an inverted index."""
    item_kws = set(item.get("tags", [])) | set(extract_keywords(item.get("title", ""), item.get("description", "")))
    if not item_kws:
        return []

    same_source = item.get("source", "")
    candidate_scores: dict[str, float] = {}

    for kw in item_kws:
        for other in inverted_index.get(kw, []):
            if other["id"] == item["id"]:
                continue
            candidate_scores[other["id"]] = candidate_scores.get(other["id"], 0) + 1

    scored = []
    for other_id, overlap in candidate_scores.items():
        other = item_by_id.get(other_id)
        if not other:
            continue
        source_boost = 1.5 if other.get("source") == same_source else 1.0
        quality = other.get("quality_score", 50)
        scored.append((overlap * source_boost * (quality / 100), other_id))

    scored.sort(key=lambda x: x[0], reverse=True)
    return [iid for _, iid in scored[:top_n]]


def main():
    if not FEED_PATH.exists():
        print("[Enrich] feed.json not found, skipping")
        return

    feed = json.loads(FEED_PATH.read_text())
    items = feed.get("items", [])

    summaries = {}
    if SUMMARIES_PATH.exists():
        summaries = json.loads(SUMMARIES_PATH.read_text())

    max_score = max((i.get("score", 0) for i in items), default=1)
    max_comments = max((i.get("comments", 0) for i in items), default=1)

    # First pass: enrich each item
    for item in items:
        domain = extract_domain(item.get("url", ""))
        item["domain"] = domain
        dtag = domain_tag(domain)

        source = item.get("source", "")
        source_tag = source.replace("_", "-")

        keyword_tags = extract_keywords(item.get("title", ""), item.get("description", ""))

        existing_tags = set(t.lower() for t in item.get("tags", []) if t)
        new_tags = {dtag, source_tag} | set(keyword_tags)
        # Merge and normalize: lowercase, hyphen-separated, deduped
        merged = sorted(
            set(
                re.sub(r"[\s_]+", "-", t).strip("-")
                for t in (existing_tags | new_tags)
                if t and len(t) >= 2
            )
        )
        item["tags"] = merged

        has_summary = bool(summaries.get(item.get("id", ""), {}).get("summary_zh"))
        item["quality_score"] = compute_quality_score(item, has_summary, max_score, max_comments)

    # Second pass: find related items
    id_to_item = {i["id"]: i for i in items}
    inverted_index = build_inverted_index(items)
    for item in items:
        related = find_related(item, inverted_index, id_to_item)
        item["related_ids"] = related

    FEED_PATH.write_text(json.dumps(feed, indent=2, ensure_ascii=False), encoding="utf-8")

    # Also update digest.json daily items with enriched metadata
    if DIGEST_PATH.exists():
        digest = json.loads(DIGEST_PATH.read_text())
        updated = 0
        for item in digest.get("daily", {}).get("items", []):
            enriched = id_to_item.get(item.get("id", ""))
            if enriched:
                item["domain"] = enriched.get("domain", "")
                item["tags"] = enriched.get("tags", [])
                item["quality_score"] = enriched.get("quality_score", 0)
                item["related_ids"] = enriched.get("related_ids", [])
                updated += 1
        DIGEST_PATH.write_text(json.dumps(digest, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"[Enrich] Updated {updated} items in digest.json")

    # Report
    tag_counts = Counter()
    for item in items:
        tag_counts.update(item.get("tags", []))

    print(f"[Enrich] {len(items)} items enriched")
    print(f"[Enrich] {len(tag_counts)} unique tags, top: {tag_counts.most_common(10)}")
    print(f"[Enrich] avg quality score: {sum(i.get('quality_score', 0) for i in items) / len(items):.1f}")


if __name__ == "__main__":
    main()
