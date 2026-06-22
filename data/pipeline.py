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

    # Step 1: Fetch
    fetch_scripts = sorted(FETCH_DIR.glob("fetch_*.py"))
    if args.skip_fetch:
        print(f"\n[Pipeline] Skipping fetch ({len(fetch_scripts)} sources)")
    else:
        print(f"\n[Pipeline] Fetching from {len(fetch_scripts)} sources...")
        for script in fetch_scripts:
            if not args.dry_run:
                run_script(script)

    # Step 2: Aggregate
    agg_script = PROCESS_DIR / "aggregate.py"
    if not args.dry_run and agg_script.exists():
        run_script(agg_script)

    # Step 3: Summarize
    sum_script = PROCESS_DIR / "summarize.py"
    if not args.skip_summarize and not args.dry_run and sum_script.exists():
        run_script(sum_script)

    # Step 3b: Build trends
    trends_script = PROCESS_DIR / "build_trends.py"
    if not args.dry_run and trends_script.exists():
        run_script(trends_script)

    # Step 4: Sync to app
    app_data_dir = BASE_DIR.parent / "app" / "src" / "data"
    if not args.dry_run and FINAL_DIR.exists():
        import shutil
        app_data_dir.mkdir(parents=True, exist_ok=True)
        for f in FINAL_DIR.glob("*.json"):
            shutil.copy2(f, app_data_dir / f.name)
            print(f"[Pipeline] Synced {f.name}")

    elapsed = (datetime.now(timezone.utc) - start).total_seconds()
    print(f"\n[Pipeline] Done in {elapsed:.1f}s")


if __name__ == "__main__":
    main()
