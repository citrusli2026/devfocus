#!/usr/bin/env python3
"""Unit tests for enrich.py helpers."""

import unittest
from datetime import datetime, timezone

from enrich import (
    domain_tag,
    extract_domain,
    extract_keywords,
    compute_quality_score,
    PLURAL_MAP,
    TAG_DENYLIST,
    STOP,
    GENERIC,
)


class TestDomainHelpers(unittest.TestCase):
    def test_extract_domain_strips_www(self):
        self.assertEqual(extract_domain("https://www.example.com/path"), "example.com")

    def test_extract_domain_lowercases(self):
        self.assertEqual(extract_domain("https://GitHub.com/Repo"), "github.com")

    def test_domain_tag_known(self):
        self.assertEqual(domain_tag("github.com"), "github")
        self.assertEqual(domain_tag("news.ycombinator.com"), "hackernews")

    def test_domain_tag_unknown_is_empty(self):
        # Unknown domains should not leak into tags as noise.
        self.assertEqual(domain_tag("some-news-site.com"), "")


class TestKeywordExtraction(unittest.TestCase):
    def test_extracts_tech_keyword(self):
        kws = extract_keywords("A new AI model from OpenAI", "")
        self.assertIn("ai", kws)
        self.assertIn("openai", kws)

    def test_ignores_stop_and_generic_words(self):
        kws = extract_keywords("The system is built for users", "")
        for w in ("the", "is", "for", "system", "built", "users"):
            self.assertNotIn(w, kws, f"{w} should be filtered")

    def test_plurals_are_mapped(self):
        # Verify common plurals in the map produce singular forms.
        self.assertEqual(PLURAL_MAP.get("agents"), "agent")
        self.assertEqual(PLURAL_MAP.get("frameworks"), "framework")

    def test_denylisted_tags_not_used(self):
        self.assertIn("blog", TAG_DENYLIST)
        self.assertIn("new", TAG_DENYLIST)


class TestQualityScore(unittest.TestCase):
    def test_perfect_item_scores_high(self):
        item = {
            "score": 1000,
            "comments": 500,
            "time": datetime.now(timezone.utc).isoformat(),
        }
        qs = compute_quality_score(item, has_summary=True, max_score=1000, max_comments=500)
        self.assertGreaterEqual(qs, 90)
        self.assertLessEqual(qs, 100)

    def test_old_item_without_summary_scores_low(self):
        old = datetime(2025, 1, 1, tzinfo=timezone.utc).isoformat()
        item = {"score": 10, "comments": 0, "time": old}
        qs = compute_quality_score(item, has_summary=False, max_score=1000, max_comments=500)
        self.assertLess(qs, 50)


if __name__ == "__main__":
    unittest.main()
