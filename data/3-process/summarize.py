#!/usr/bin/env python3
from __future__ import annotations

"""Generate bilingual summaries for digest items.

Priority:
  1. Existing summaries in summaries.json (skip if already have)
  2. LLM API (if DEEPSEEK_API_KEY or OPENAI_API_KEY env var set)
  3. Template fallback (low quality, last resort)
"""

import json
import os
import sys
import time
import urllib.request
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
FINAL_DIR = BASE_DIR / "4-final"
SUMMARIES_PATH = FINAL_DIR / "summaries.json"

# LLM config from environment variables (never hardcoded)
LLM_PROVIDERS = [
    {
        "name": "deepseek",
        "base_url": "https://api.deepseek.com",
        "api_key_env": "DEEPSEEK_API_KEY",
        "model": "deepseek-v4-flash",
    },
    {
        "name": "openai",
        "base_url": "https://api.openai.com/v1",
        "api_key_env": "OPENAI_API_KEY",
        "model": "gpt-4o-mini",
    },
]


def call_llm(base_url: str, api_key: str, model: str, prompt: str) -> str:
    """Call LLM API, return response text or empty string."""
    url = f"{base_url}/chat/completions"
    body = json.dumps({
        "model": model,
        "messages": [
            {"role": "system", "content": (
                "You are a senior tech news editor. Write concise, scannable summaries. "
                "Output ONLY valid JSON, no markdown fences."
            )},
            {"role": "user", "content": prompt},
        ],
        "temperature": 0.3,
        "max_tokens": 3000,
    }).encode()

    req = urllib.request.Request(url, data=body, headers={
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}",
    })

    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            data = json.loads(resp.read().decode())
            return data["choices"][0]["message"]["content"].strip()
    except Exception as e:
        print(f"  [WARN] LLM call failed: {e}", file=sys.stderr)
        return ""


def build_prompt(items: list[dict]) -> str:
    """Build summarization prompt for a batch of items."""
    lines = []
    for i, item in enumerate(items):
        desc = item.get("description", "")[:150]
        lines.append(f"{i+1}. id={item['id']} | title={item['title']} | source={item['source']} | desc={desc}")
    return f"""For each item below, write a concise summary in Chinese (summary_zh) and English (summary_en).

FORMAT RULES:
- Chinese: ~100-200 characters, narrative style (记叙文), describe what it is and why it matters
- English: ~80-120 words, narrative style, describe what it is and why it matters
- Use natural, flowing sentences — NOT bullet points or key-value pairs
- Write like a tech blogger explaining to a friend
- Focus on: what problem it solves, what's interesting about it, who would benefit

Items:
{chr(10).join(lines)}

Return a JSON array:
[{{"id": "xxx", "summary_zh": "中文摘要", "summary_en": "English summary"}}, ...]

ONLY the JSON array, nothing else."""


def parse_llm_response(text: str) -> list[dict]:
    """Parse LLM response, handling markdown fences."""
    clean = text.strip()
    if clean.startswith("```"):
        clean = clean.split("\n", 1)[1] if "\n" in clean else clean[3:]
        clean = clean.rsplit("```", 1)[0]
    return json.loads(clean.strip())


def get_llm_provider():
    """Find first available LLM provider with API key set."""
    for provider in LLM_PROVIDERS:
        key = os.environ.get(provider["api_key_env"], "")
        # Validate key looks real (starts with sk-)
        if not key.startswith("sk-"):
            key = ""
        # Also try local key file (for development)
        if not key:
            key_file = BASE_DIR / ".deepseek_key"
            if key_file.exists():
                key = key_file.read_text().strip()
        if key:
            return {**provider, "api_key": key}
    return None


def template_summary(item: dict) -> tuple[str, str]:
    """Low-quality template fallback."""
    title = item.get("title", "")
    source = item.get("source", "")
    desc = item.get("description", "")[:100]
    if source == "github_trending":
        name = title.split("/")[-1] if "/" in title else title
        return (f"开源项目 {name}" + (f" — {desc}" if desc else "。"),
                f"Open-source project {name}" + (f" — {desc}" if desc else "."))
    return f"HN 热门：{title}", f"Trending on HN: {title}"


def main():
    digest_path = FINAL_DIR / "digest.json"
    if not digest_path.exists():
        print("[SUM] No digest.json found.")
        sys.exit(1)

    digest = json.loads(digest_path.read_text())

    existing: dict[str, dict] = {}
    if SUMMARIES_PATH.exists():
        existing = json.loads(SUMMARIES_PATH.read_text())

    # Collect unique items needing summaries
    all_items: dict[str, dict] = {}
    for key in ["daily"]:
        for item in digest[key]["items"]:
            all_items[item["id"]] = item

    need = {id: item for id, item in all_items.items()
            if not existing.get(id, {}).get("summary_zh")
            or len(existing[id].get("summary_zh", "")) < 50
            or existing[id]["summary_zh"].startswith("HN 热门")
            or existing[id]["summary_zh"].startswith("开源项目")}

    if not need:
        print("[SUM] All items have good summaries.")
        # Still apply existing summaries to digest
        for key in ["daily"]:
            for item in digest[key]["items"]:
                s = existing.get(item["id"])
                if s:
                    item["summary_zh"] = s.get("summary_zh", "")
                    item["summary_en"] = s.get("summary_en", "")
        digest_path.write_text(json.dumps(digest, indent=2, ensure_ascii=False))
        return

    print(f"[SUM] {len(need)} items need summaries")

    # Try LLM first
    provider = get_llm_provider()
    summaries: dict[str, dict] = {}

    if provider:
        print(f"[SUM] Using {provider['name']} API ({provider['model']})...")
        need_list = list(need.values())

        # Batch in groups of 5
        for i in range(0, len(need_list), 5):
            batch = need_list[i:i+5]
            prompt = build_prompt(batch)
            result = call_llm(provider["base_url"], provider["api_key"], provider["model"], prompt)

            if result:
                try:
                    parsed = parse_llm_response(result)
                    for entry in parsed:
                        if isinstance(entry, dict) and "id" in entry:
                            summaries[entry["id"]] = {
                                "summary_zh": entry.get("summary_zh", ""),
                                "summary_en": entry.get("summary_en", ""),
                            }
                    print(f"  Batch {i//5+1}: {len(parsed)} summaries")
                except json.JSONDecodeError as e:
                    print(f"  [WARN] JSON parse error: {e}")

            if i + 5 < len(need_list):
                time.sleep(1)
    else:
        print("[SUM] No LLM API key found (set DEEPSEEK_API_KEY or OPENAI_API_KEY)")
        print("[SUM] Falling back to template summaries")

    # Fallback: template for any still missing
    for id, item in need.items():
        if id not in summaries:
            zh, en = template_summary(item)
            summaries[id] = {"summary_zh": zh, "summary_en": en}

    # Merge into existing
    existing.update(summaries)

    # Apply to digest
    for key in ["daily"]:
        for item in digest[key]["items"]:
            s = existing.get(item["id"])
            if s:
                item["summary_zh"] = s.get("summary_zh", "")
                item["summary_en"] = s.get("summary_en", "")

    # Save
    digest_path.write_text(json.dumps(digest, indent=2, ensure_ascii=False))
    SUMMARIES_PATH.write_text(json.dumps(existing, indent=2, ensure_ascii=False))

    llm_count = len([s for s in summaries.values()
                     if not s["summary_zh"].startswith("HN 热门")
                     and not s["summary_zh"].startswith("开源项目")
                     and len(s["summary_zh"]) >= 50])
    print(f"[SUM] Done: {llm_count} LLM + {len(summaries)-llm_count} template = {len(summaries)} total")


if __name__ == "__main__":
    main()
