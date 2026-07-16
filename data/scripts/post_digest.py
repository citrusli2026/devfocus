#!/usr/bin/env python3
"""Post daily digest to social channels (Telegram, extensible to Twitter/X).

Usage:
  # Telegram (set TELEGRAM_BOT_TOKEN + TELEGRAM_CHAT_ID)
  python3 post_digest.py

  # Dry-run (print what would be posted)
  python3 post_digest.py --dry-run
"""

import argparse
import json
import os
import sys
import urllib.request
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
FINAL_DIR = BASE_DIR / "4-final"
SITE_URL = "https://www.devfocus.cc"

SOURCE_ICONS = {
    "hackernews": "🔥",
    "github_trending": "⭐",
    "producthunt": "🚀",
    "juejin": "📘",
    "zhihu": "💬",
    "36kr": "📊",
    "infoq": "📰",
    "v2ex": "💭",
}

SOURCE_LABELS = {
    "hackernews": "HN",
    "github_trending": "GitHub",
    "producthunt": "PH",
    "juejin": "掘金",
    "zhihu": "知乎",
    "36kr": "36氪",
    "infoq": "InfoQ",
    "v2ex": "V2EX",
}


def build_digest_text(items: list[dict], date: str) -> str:
    """Build a concise digest text for social posting."""
    # Group by source
    by_source: dict[str, list[dict]] = {}
    for item in items:
        by_source.setdefault(item["source"], []).append(item)

    lines = [f"📰 DevFocus 每日精选 — {date}\n"]

    for source, sitems in by_source.items():
        icon = SOURCE_ICONS.get(source, "📌")
        label = SOURCE_LABELS.get(source, source)
        lines.append(f"\n{icon} {label} Top {len(sitems)}:")
        for item in sitems[:3]:  # Top 3 per source
            title = item.get("title", "")
            if len(title) > 60:
                title = title[:57] + "..."
            lines.append(f"  • {title}")

    lines.append(f"\n🔗 完整榜单: {SITE_URL}")
    return "\n".join(lines)


def post_telegram(bot_token: str, chat_id: str, text: str) -> bool:
    """Send message via Telegram Bot API. Handles message splitting if needed."""
    # Telegram has 4096 char limit per message
    max_len = 4000
    parts = [text[i:i+max_len] for i in range(0, len(text), max_len)]

    for part in parts:
        url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        body = json.dumps({
            "chat_id": chat_id,
            "text": part,
            "parse_mode": "HTML",
            "disable_web_page_preview": False,
        }).encode()

        req = urllib.request.Request(url, data=body, headers={
            "Content-Type": "application/json",
        })
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                result = json.loads(resp.read().decode())
                if not result.get("ok"):
                    print(f"[POST] Telegram error: {result.get('description', 'unknown')}")
                    return False
        except Exception as e:
            print(f"[POST] Telegram request failed: {e}")
            return False

    print(f"[POST] Telegram: {len(parts)} part(s) sent")
    return True


def main():
    parser = argparse.ArgumentParser(description="Post daily digest to social channels")
    parser.add_argument("--dry-run", action="store_true", help="Print digest without posting")
    args = parser.parse_args()

    digest_path = FINAL_DIR / "digest.json"
    if not digest_path.exists():
        print("[POST] No digest.json found, skipping")
        return

    digest = json.loads(digest_path.read_text())
    daily = digest.get("daily", {})
    items = daily.get("items", [])
    date = daily.get("date", "")

    if not items:
        print("[POST] No daily items, skipping")
        return

    text = build_digest_text(items, date)

    if args.dry_run:
        print("=" * 50)
        print(text)
        print("=" * 50)
        print(f"\nLength: {len(text)} chars")
        return

    # --- Telegram ---
    bot_token = os.environ.get("TELEGRAM_BOT_TOKEN", "")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID", "")
    if bot_token and chat_id:
        post_telegram(bot_token, chat_id, text)
    else:
        print("[POST] TELEGRAM_BOT_TOKEN / TELEGRAM_CHAT_ID not set, skipping Telegram")
        print("[POST] Set these env vars to enable Telegram posting")

    # --- Future: Twitter/X ---
    # if os.environ.get("TWITTER_API_KEY"):
    #     post_twitter(...)

    print("[POST] Done")


if __name__ == "__main__":
    main()
