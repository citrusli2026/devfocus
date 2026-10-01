#!/usr/bin/env python3
"""历史快照连续性检查：最近 N 天有空洞就报警。

为什么单独一个脚本：空洞曾经是完全静默的——2026-09-28 的快照因为定时任务延迟
跨过 UTC 零点被吞掉，管线依旧全绿，只在很久以后被人从趋势热力图上发现少一列。
这里把空洞变成 GitHub Actions 里可见的 ::warning:: 注解（本地跑则只是打印）。

退出码恒为 0：空洞是「需要被看见」的问题，不该让当天的数据管线变红——
管线红了就不会提交数据，反而制造更大的空洞。

用法：
    python3 scripts/check_history.py [--days 30]
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "3-process"))
from _shared import find_history_gaps  # noqa: E402

DATA_DIR = Path(__file__).resolve().parent.parent
HISTORY_DIR = DATA_DIR / "5-history"


def main() -> int:
    parser = argparse.ArgumentParser(description="Check history snapshot continuity")
    parser.add_argument("--days", type=int, default=30, help="检查窗口（默认 30 天）")
    args = parser.parse_args()

    if not HISTORY_DIR.exists():
        print(f"[History] {HISTORY_DIR} 不存在，跳过检查")
        return 0

    stems = [f.stem for f in HISTORY_DIR.glob("*.json")]
    gaps = find_history_gaps(stems, args.days)
    print(f"[History] {len(stems)} 个快照，检查最近 {args.days} 天窗口："
          f"{'连续，无空洞' if not gaps else f'发现 {len(gaps)} 天空洞'}")

    if gaps:
        joined = ", ".join(gaps)
        print(f"[History] WARN 缺失快照: {joined}")
        # GitHub Actions 注解：在 run 页面以 warning 形式高亮
        print(f"::warning title=History snapshot gap::{len(gaps)} day(s) missing: {joined}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
