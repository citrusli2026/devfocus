#!/usr/bin/env python3
"""Unit tests for summarize.py helpers（含历次修复的回归用例）。"""

import unittest

from summarize import ensure_digest_summaries, prune_unresolved_empty


class TestEnsureDigestSummaries(unittest.TestCase):
    def test_fills_missing_daily_and_monthly(self):
        digest = {
            "daily": {
                "items": [
                    {"id": "d1", "title": "Daily title", "source": "hackernews",
                     "summary_zh": "", "summary_en": ""},
                ]
            },
            "monthly": {
                "items": [
                    {"id": "m1", "title": "owner/repo", "source": "github_trending"},
                ]
            },
        }
        existing = {}
        ensure_digest_summaries(digest, existing)

        self.assertTrue(digest["daily"]["items"][0]["summary_zh"])
        self.assertTrue(digest["daily"]["items"][0]["summary_en"])
        self.assertTrue(digest["monthly"]["items"][0]["summary_zh"])
        self.assertTrue(digest["monthly"]["items"][0]["summary_en"])
        self.assertIn("d1", existing)
        self.assertIn("m1", existing)
        self.assertIn("input_hash", existing["d1"])
        self.assertIn("input_hash", existing["m1"])

    def test_keeps_existing_summary(self):
        digest = {
            "daily": {
                "items": [
                    {"id": "d1", "title": "T", "source": "hackernews",
                     "summary_zh": "已有摘要", "summary_en": "Existing"},
                ]
            },
            "monthly": {"items": []},
        }
        existing = {
            "d1": {"summary_zh": "已有摘要", "summary_en": "Existing", "input_hash": "abc"},
        }
        ensure_digest_summaries(digest, existing)
        self.assertEqual(digest["daily"]["items"][0]["summary_zh"], "已有摘要")
        self.assertEqual(existing["d1"]["summary_zh"], "已有摘要")


class TestPruneUnresolvedEmpty(unittest.TestCase):
    def test_prunes_only_dead_entries(self):
        existing = {
            "dead": {"summary_zh": "", "summary_en": ""},
            "has_hash": {"summary_zh": "", "summary_en": "", "input_hash": "abc"},
            "has_failed": {"summary_zh": "", "summary_en": "", "failed_at": "2026-08-16T00:00:00+00:00"},
            "keep": {"summary_zh": "ok", "summary_en": "ok"},
        }
        unresolved = {"dead", "has_hash", "has_failed", "not_in_existing"}
        pruned = prune_unresolved_empty(existing, unresolved)

        self.assertEqual(pruned, 1)
        self.assertNotIn("dead", existing)
        self.assertIn("has_hash", existing)
        self.assertIn("has_failed", existing)
        self.assertIn("keep", existing)

    def test_prune_empty_set_returns_zero(self):
        existing = {"a": {"summary_zh": "", "summary_en": ""}}
        self.assertEqual(prune_unresolved_empty(existing, set()), 0)
        self.assertIn("a", existing)


if __name__ == "__main__":
    unittest.main()
