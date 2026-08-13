#!/usr/bin/env python3
from __future__ import annotations

"""Pipeline orchestrator. Runs fetch → aggregate → summarize → sync."""

import argparse
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
FETCH_DIR = BASE_DIR / "1-fetch"
PROCESS_DIR = BASE_DIR / "3-process"
FINAL_DIR = BASE_DIR / "4-final"
SCRIPTS_DIR = BASE_DIR / "scripts"

# 关键步骤失败时 pipeline 以非零退出（其余步骤失败仅记 WARN 并计入汇总）
CRITICAL_STEPS = {"aggregate.py"}


def run_script(script_path: Path, args: list[str] | None = None):
    cmd = [sys.executable, str(script_path)] + (args or [])
    print(f"\n{'='*60}\nRunning: {script_path.name}\n{'='*60}")
    result = subprocess.run(cmd, cwd=BASE_DIR)
    if result.returncode != 0:
        print(f"[WARN] {script_path.name} exited with code {result.returncode}")
    return result.returncode


def main():
    parser = argparse.ArgumentParser(description="DevFocus data pipeline")
    parser.add_argument("--skip-fetch", action="store_true")
    parser.add_argument("--skip-summarize", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    start = datetime.now(timezone.utc)
    print(f"[Pipeline] Starting at {start.isoformat()}")
    results: list[tuple[str, int]] = []

    def step(script_path: Path):
        results.append((script_path.name, run_script(script_path)))

    # Step 1: Fetch
    fetch_scripts = sorted(FETCH_DIR.glob("fetch_*.py"))
    if args.skip_fetch:
        print(f"\n[Pipeline] Skipping fetch ({len(fetch_scripts)} sources)")
    else:
        print(f"\n[Pipeline] Fetching from {len(fetch_scripts)} sources...")
        for script in fetch_scripts:
            if not args.dry_run:
                step(script)

    # Step 2: Aggregate
    agg_script = PROCESS_DIR / "aggregate.py"
    if not args.dry_run and agg_script.exists():
        step(agg_script)

    # Step 3: Summarize
    sum_script = PROCESS_DIR / "summarize.py"
    if not args.skip_summarize and not args.dry_run and sum_script.exists():
        step(sum_script)

    # Step 3b: Enrich items (tags, domain, quality score, related items)
    enrich_script = PROCESS_DIR / "enrich.py"
    if not args.dry_run and enrich_script.exists():
        step(enrich_script)

    # Step 3c: Build stats
    stats_script = PROCESS_DIR / "build_stats.py"
    if not args.dry_run and stats_script.exists():
        step(stats_script)

    # Step 3d: Build topic trends (非关键步骤，失败不阻塞)
    trends_script = PROCESS_DIR / "build_trends.py"
    if not args.dry_run and trends_script.exists():
        step(trends_script)

    # Step 3e: Build search index
    search_index_script = PROCESS_DIR / "build_search_index.py"
    if not args.dry_run and search_index_script.exists():
        step(search_index_script)

    # Step 4: Sync to app
    app_data_dir = BASE_DIR.parent / "app" / "src" / "data"
    app_public_dir = BASE_DIR.parent / "app" / "public"
    if not args.dry_run and FINAL_DIR.exists():
        import shutil
        # 不进入 src/data 的文件：
        # - summaries.json：仅管线内部使用（enrich 合并摘要），前端零引用（1.8MB）
        # - search-index.json：运行时从 public/ 拉取，src/data 副本冗余（334KB×2）
        EXCLUDED_FROM_SRC_DATA = {"summaries.json", "search-index.json"}
        app_data_dir.mkdir(parents=True, exist_ok=True)
        for f in FINAL_DIR.glob("*.json"):
            if f.name in EXCLUDED_FROM_SRC_DATA:
                continue
            shutil.copy2(f, app_data_dir / f.name)
            print(f"[Pipeline] Synced {f.name}")
        # Search index goes to public/ so it is fetched at runtime, not bundled
        search_index = FINAL_DIR / "search-index.json"
        if search_index.exists():
            app_public_dir.mkdir(parents=True, exist_ok=True)
            shutil.copy2(search_index, app_public_dir / search_index.name)
            print(f"[Pipeline] Synced {search_index.name} to public/")

    # Step 5: Generate RSS feed
    rss_script = SCRIPTS_DIR / "generate_rss.py"
    if not args.dry_run and rss_script.exists():
        step(rss_script)

    # Step 6: Validate final data (失败视为 WARN，计入结尾汇总)
    validate_script = SCRIPTS_DIR / "validate_data.py"
    if not args.dry_run and validate_script.exists():
        step(validate_script)

    elapsed = (datetime.now(timezone.utc) - start).total_seconds()
    print(f"\n[Pipeline] Done in {elapsed:.1f}s")

    failed = [name for name, rc in results if rc != 0]
    if failed:
        print(f"[Pipeline] Failed steps: {', '.join(failed)}")
    else:
        print("[Pipeline] All steps succeeded")

    critical_failed = [name for name in failed if name in CRITICAL_STEPS]
    if critical_failed:
        print(f"[Pipeline] CRITICAL step failed: {', '.join(critical_failed)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
