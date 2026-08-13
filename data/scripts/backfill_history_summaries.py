#!/usr/bin/env python3
"""Backfill bilingual summaries into existing history snapshots.

⚠️ 一次性手动工具（未被 pipeline.py 调用）：日常回填由 summarize.py 的
backfill_history_summaries() 完成（语义略不同——管线版对今日快照覆盖
最新值，本脚本只填空不覆盖）。仅当你需要手动批量回填历史快照时使用。

Reads summaries.json and applies summary_zh/summary_en to matching items in
5-history/*.json snapshots. This makes archived daily pages retain summaries
for items that were ever featured in the digest.
"""

from __future__ import annotations

import json
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
HISTORY_DIR = BASE_DIR / "5-history"
SUMMARIES_PATH = BASE_DIR / "4-final" / "summaries.json"


def main():
    if not SUMMARIES_PATH.exists():
        print("[BACKFILL] No summaries.json found, skipping")
        return

    summaries = json.loads(SUMMARIES_PATH.read_text())
    if not HISTORY_DIR.exists():
        print("[BACKFILL] No history directory found, skipping")
        return

    updated_files = 0
    for f in sorted(HISTORY_DIR.glob("*.json")):
        try:
            data = json.loads(f.read_text())
        except Exception:
            continue

        changed = False
        for key in ("digest_items", "items"):
            for item in data.get(key, []):
                iid = item.get("id", "")
                s = summaries.get(iid)
                if s and (not item.get("summary_zh") or not item.get("summary_en")):
                    item["summary_zh"] = s.get("summary_zh", "")
                    item["summary_en"] = s.get("summary_en", "")
                    changed = True

        if changed:
            f.write_text(json.dumps(data, indent=2, ensure_ascii=False))
            updated_files += 1

    print(f"[BACKFILL] Updated {updated_files} history snapshots with summaries")


if __name__ == "__main__":
    main()
