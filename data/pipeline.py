#!/usr/bin/env python3
"""Pipeline orchestrator. Runs fetch → process → final in sequence."""

from __future__ import annotations

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
    """Run a Python script and return exit code."""
    cmd = [sys.executable, str(script_path)] + (args or [])
    print(f"\n{'='*60}")
    print(f"Running: {' '.join(cmd)}")
    print(f"{'='*60}")
    result = subprocess.run(cmd, cwd=BASE_DIR)
    if result.returncode != 0:
        print(f"[WARN] {script_path.name} exited with code {result.returncode}")
    return result.returncode


def main():
    parser = argparse.ArgumentParser(description="DevPulse data pipeline")
    parser.add_argument("--skip-fetch", action="store_true", help="Skip fetch step")
    parser.add_argument("--dry-run", action="store_true", help="Print what would run without executing")
    args = parser.parse_args()

    start = datetime.now(timezone.utc)
    print(f"[Pipeline] Starting at {start.isoformat()}")

    # Step 1: Fetch
    fetch_scripts = sorted(FETCH_DIR.glob("fetch_*.py"))
    if args.skip_fetch:
        print(f"\n[Pipeline] Skipping fetch ({len(fetch_scripts)} scripts)")
    else:
        print(f"\n[Pipeline] Fetching from {len(fetch_scripts)} sources...")
        for script in fetch_scripts:
            if args.dry_run:
                print(f"  [DRY] Would run: {script.name}")
            else:
                run_script(script)

    # Step 2: Process
    process_script = PROCESS_DIR / "aggregate.py"
    if process_script.exists():
        if args.dry_run:
            print(f"  [DRY] Would run: aggregate.py")
        else:
            run_script(process_script)
    else:
        print(f"[WARN] {process_script} not found, skipping")

    # Step 3: Copy to app
    app_data_dir = BASE_DIR.parent / "app" / "src" / "data"
    if not args.dry_run and FINAL_DIR.exists():
        app_data_dir.mkdir(parents=True, exist_ok=True)
        import shutil
        for f in FINAL_DIR.glob("*.json"):
            dest = app_data_dir / f.name
            shutil.copy2(f, dest)
            print(f"[Pipeline] Synced {f.name} → {dest}")

    elapsed = (datetime.now(timezone.utc) - start).total_seconds()
    print(f"\n[Pipeline] Done in {elapsed:.1f}s")


if __name__ == "__main__":
    main()
