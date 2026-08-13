#!/usr/bin/env python3
"""Unit tests for enrich.py helpers（含历次修复的回归用例）。"""

import unittest
from datetime import datetime, timezone

from _shared import parse_time
from enrich import (
    SOURCE_TAGS,
    _content_kws,
    build_inverted_index,
    domain_tag,
    extract_domain,
    extract_keywords,
    find_related,
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

    def test_extract_domain_removes_only_prefix_www(self):
        # 回归：replace 删所有 "www." 会把中间域名段也删掉
        self.assertEqual(extract_domain("https://www.news.www.example.com/x"),
                         "news.www.example.com")

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

    def test_ascii_tech_keyword_word_boundary(self):
        # 回归：整词边界——"ai" 不得命中 sailing/said，"go" 不得命中 google
        kws = extract_keywords("Understanding Sailing and Trains for Beginners", "")
        self.assertNotIn("ai", kws, "'ai' must not match inside 'sailing/trains'")
        kws = extract_keywords("Google launches a new runtime", "")
        self.assertNotIn("go", kws, "'go' must not match inside 'google'")
        # 独立词 Go（语言）应命中
        kws = extract_keywords("Building CLI tools with Go", "")
        self.assertIn("go", kws)

    def test_cjk_fragment_filtered(self):
        # 回归：中文连续段整体成词，不产 "正式版发" 类残缺窗口
        kws = extract_keywords("小米正式版发布", "")
        self.assertIn("小米正式版发布", kws)
        self.assertNotIn("正式版发", kws)
        self.assertNotIn("式版发布", kws)

    def test_cjk_question_sentence_skipped(self):
        # 回归：疑问句式（如何/为什么）整段跳过，仅保留技术词
        kws = extract_keywords("如何看待国产大模型", "")
        self.assertIn("大模型", kws)
        self.assertNotIn("如何看待", kws)
        self.assertNotIn("何看待国产大", kws)

    def test_generic_potential_filtered(self):
        # 回归：GENERIC 词表 " potential" 前导空格修复后应生效
        kws = extract_keywords("The potential of this API is huge", "")
        self.assertNotIn("potential", kws)

    def test_multiword_tech_tag_normalized(self):
        # "machine learning" 产出（后续归一化为 machine-learning）
        kws = extract_keywords("A practical machine learning tutorial", "")
        self.assertIn("machine learning", kws)


class TestParseTime(unittest.TestCase):
    def test_iso_string(self):
        dt = parse_time("2026-08-13T01:00:00+00:00")
        self.assertEqual(dt.year, 2026)
        self.assertEqual(dt.month, 8)

    def test_epoch_seconds_and_millis(self):
        self.assertEqual(parse_time(1_750_000_000).year, 2025)
        self.assertEqual(parse_time(1_750_000_000_000).year, 2025)

    def test_epoch_micros(self):
        # 回归：微秒时间戳一次除法后仍 >1e12，旧逻辑解释成 1970 附近
        self.assertEqual(parse_time(1_750_000_000_000_000).year, 2025)

    def test_invalid(self):
        self.assertIsNone(parse_time(""))
        self.assertIsNone(parse_time(None))
        self.assertIsNone(parse_time("not-a-date"))


class TestRelatedItems(unittest.TestCase):
    def _mk(self, iid, source, tags, title=""):
        return {"id": iid, "source": source, "tags": tags, "title": title, "description": "",
                "quality_score": 80}

    def test_source_tags_excluded_from_related(self):
        # 回归：源/域级标签不参与相关匹配（此前 hackernews 桶含 3000+ 条，
        # find_related 退化为 O(n²) 且结果被同源条目主导）
        hn1 = self._mk("hn-1", "hackernews", ["hackernews", "llm"], "New LLM paper")
        hn2 = self._mk("hn-2", "hackernews", ["hackernews"], "Something else")
        gh = self._mk("gh-1", "github_trending", ["github", "llm"], "LLM repo")
        items = [hn1, hn2, gh]
        index = build_inverted_index(items)
        related = find_related(hn1, index, {i["id"]: i for i in items})
        self.assertIn("gh-1", related)
        self.assertNotIn("hn-2", related)  # 仅共享源标签的不应相关

    def test_content_kws_excludes_source_tags(self):
        kws = _content_kws(self._mk("x", "hackernews", ["hackernews", "ai"], "AI stuff"))
        self.assertNotIn("hackernews", kws)
        self.assertIn("ai", kws)


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
