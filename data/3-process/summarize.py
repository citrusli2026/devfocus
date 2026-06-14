#!/usr/bin/env python3
from __future__ import annotations

"""Generate bilingual summaries for digest items.
Uses template-based generation (no LLM API needed).
Falls back to web_extract content if available."""

import json
import re
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
FINAL_DIR = BASE_DIR / "4-final"
SUMMARIES_PATH = FINAL_DIR / "summaries.json"


def extract_keywords(title: str) -> list[str]:
    """Extract meaningful keywords from title."""
    stop = {"a", "an", "the", "is", "are", "was", "were", "in", "on", "at", "to", "for",
            "of", "and", "or", "but", "not", "with", "from", "by", "as", "it", "its",
            "this", "that", "be", "have", "has", "had", "do", "does", "did", "will",
            "would", "could", "should", "may", "might", "can", "shall", "show", "hn"}
    words = re.findall(r'[A-Za-z][\w.-]+', title)
    return [w for w in words if w.lower() not in stop]


def template_summary(item: dict) -> tuple[str, str]:
    """Generate a template-based bilingual summary from title + source."""
    title = item.get("title", "")
    source = item.get("source", "")
    desc = item.get("description", "")[:100]

    # For GitHub repos
    if source == "github_trending":
        name = title.split("/")[-1] if "/" in title else title
        zh = f"开源项目 {name}" + (f" — {desc}" if desc else "，在 GitHub 上 trending。")
        en = f"Open-source project {name}" + (f" — {desc}" if desc else ", trending on GitHub.")
        return zh, en

    # For HN — use title as basis
    zh = f"HN 热门：{title}"
    en = f"Trending on HN: {title}"
    return zh, en


def main():
    digest_path = FINAL_DIR / "digest.json"
    if not digest_path.exists():
        print("[SUM] No digest.json found.")
        sys.exit(1)

    digest = json.loads(digest_path.read_text())

    # Load existing summaries
    existing: dict[str, dict] = {}
    if SUMMARIES_PATH.exists():
        existing = json.loads(SUMMARIES_PATH.read_text())

    # Find items needing summaries
    all_items: dict[str, dict] = {}
    for key in ["daily", "monthly"]:
        for item in digest[key]["items"]:
            all_items[item["id"]] = item

    need_summary = {id: item for id, item in all_items.items() if not existing.get(id, {}).get("summary_zh")}

    if not need_summary:
        print("[SUM] All items already have summaries.")
        return

    print(f"[SUM] Generating summaries for {len(need_summary)} items...")

    # Generate template summaries
    new_count = 0
    for id, item in need_summary.items():
        zh, en = template_summary(item)
        existing[id] = {"summary_zh": zh, "summary_en": en}
        new_count += 1

    # Apply to digest
    for key in ["daily", "monthly"]:
        for item in digest[key]["items"]:
            s = existing.get(item["id"])
            if s:
                item["summary_zh"] = s.get("summary_zh", "")
                item["summary_en"] = s.get("summary_en", "")

    # Save
    digest_path.write_text(json.dumps(digest, indent=2, ensure_ascii=False))
    SUMMARIES_PATH.write_text(json.dumps(existing, indent=2, ensure_ascii=False))
    print(f"[SUM] Generated {new_count} template summaries")


if __name__ == "__main__":
    main()
