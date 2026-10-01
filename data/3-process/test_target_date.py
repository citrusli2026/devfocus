#!/usr/bin/env python3
"""快照日期锚定与历史空洞检测的单元测试。

回归背景（2026-09-28）：GitHub schedule 常延迟 2~4 小时，偶尔跨过 UTC 零点。
旧实现按「运行时 UTC 日期」给快照命名，于是 09-28 20:00 槽位那次运行（实际
09-29T00:12Z 起跑）把快照写成了 09-29，几个小时后真正的 09-29 运行又覆盖同一
文件——09-28 整整一天消失，前端 trends 热力图少了一整列。
"""

import unittest
from datetime import datetime, timedelta, timezone

from _shared import DEFAULT_SLOT_UTC_HOUR, find_history_gaps, resolve_target_date


def utc(*args) -> datetime:
    return datetime(*args, tzinfo=timezone.utc)


class ResolveTargetDateTest(unittest.TestCase):
    def test_default_slot_matches_daily_workflow_cron(self):
        # daily.yml 的 cron 是 '0 20 * * *'；改 cron 必须同步改常量
        self.assertEqual(DEFAULT_SLOT_UTC_HOUR, 20)

    def test_schedule_on_time_is_same_day(self):
        self.assertEqual(resolve_target_date(utc(2026, 9, 29, 20, 0), "schedule"), "2026-09-29")

    def test_schedule_delayed_within_same_day(self):
        # 观测到的典型延迟：20:00 槽位实际 22:20~23:30 起跑
        self.assertEqual(resolve_target_date(utc(2026, 9, 30, 23, 29), "schedule"), "2026-09-30")

    def test_schedule_delayed_across_midnight_stays_on_slot_day(self):
        # 事故现场：09-28 槽位的运行 09-29T00:12Z 才起跑 → 必须仍标 09-28
        self.assertEqual(resolve_target_date(utc(2026, 9, 29, 0, 12), "schedule"), "2026-09-28")

    def test_schedule_repeat_delivery_is_idempotent(self):
        # 同一槽位重复投递 → 同一天，写同一个文件，不产生新的一天
        first = resolve_target_date(utc(2026, 9, 29, 0, 12), "schedule")
        second = resolve_target_date(utc(2026, 9, 29, 1, 40), "schedule")
        self.assertEqual(first, second)

    def test_schedule_early_fire_belongs_to_previous_slot(self):
        # 槽位前提前触发（罕见）→ 归属前一槽位，宁可覆盖也不要凭空多一天
        self.assertEqual(resolve_target_date(utc(2026, 9, 29, 19, 30), "schedule"), "2026-09-28")

    def test_non_utc_input_is_normalized(self):
        # 带 +08:00 的 09-29 08:12 == UTC 09-29 00:12 → 归属 09-28 槽位
        cst = timezone(timedelta(hours=8))
        self.assertEqual(resolve_target_date(datetime(2026, 9, 29, 8, 12, tzinfo=cst), "schedule"),
                         "2026-09-28")

    def test_workflow_dispatch_uses_utc_today(self):
        # 手动触发按当天算，方便补跑当天数据
        self.assertEqual(resolve_target_date(utc(2026, 9, 29, 0, 12), "workflow_dispatch"),
                         "2026-09-29")

    def test_local_run_uses_utc_today(self):
        self.assertEqual(resolve_target_date(utc(2026, 9, 29, 0, 12), None), "2026-09-29")

    def test_custom_slot_hour(self):
        args = (utc(2026, 9, 29, 18, 0), "schedule", 17)
        self.assertEqual(resolve_target_date(*args), "2026-09-29")
        args = (utc(2026, 9, 29, 16, 0), "schedule", 17)
        self.assertEqual(resolve_target_date(*args), "2026-09-28")


class FindHistoryGapsTest(unittest.TestCase):
    @staticmethod
    def _range(start: str, days: int) -> list[str]:
        base = datetime.strptime(start, "%Y-%m-%d")
        return [(base + timedelta(days=i)).strftime("%Y-%m-%d") for i in range(days)]

    def test_contiguous_history_has_no_gaps(self):
        self.assertEqual(find_history_gaps(self._range("2026-09-01", 30), 30), [])

    def test_missing_middle_day_is_reported(self):
        days = [d for d in self._range("2026-09-01", 30) if d != "2026-09-28"]
        self.assertEqual(find_history_gaps(days, 30), ["2026-09-28"])

    def test_multiple_gaps_sorted_ascending(self):
        days = [d for d in self._range("2026-09-01", 30)
                if d not in {"2026-09-27", "2026-09-23", "2026-09-28"}]
        self.assertEqual(find_history_gaps(days, 30),
                         ["2026-09-23", "2026-09-27", "2026-09-28"])

    def test_short_history_is_not_reported_as_gap(self):
        # 项目刚上线、历史不足窗口长度 → 不把上线前的空白误报成空洞
        self.assertEqual(find_history_gaps(self._range("2026-09-27", 4), 30), [])

    def test_holes_before_window_are_ignored(self):
        # 30 天窗口内连续，窗口之外的旧空洞不再报警（已滚出前端展示范围）
        days = self._range("2026-08-01", 10) + self._range("2026-09-01", 30)
        self.assertEqual(find_history_gaps(days, 30), [])

    def test_unsorted_and_dirty_entries(self):
        days = self._range("2026-09-01", 30)
        days = list(reversed(days)) + ["tmp", "2026-09-32", ""]
        self.assertEqual(find_history_gaps(days, 30), [])

    def test_empty_input(self):
        self.assertEqual(find_history_gaps([], 30), [])

    def test_zero_window(self):
        self.assertEqual(find_history_gaps(self._range("2026-09-01", 5), 0), [])


if __name__ == "__main__":
    unittest.main()
