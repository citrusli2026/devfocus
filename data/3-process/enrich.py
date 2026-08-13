#!/usr/bin/env python3
"""Enrich feed items with derived metadata: tags, domain, quality score, related items.

Input: 4-final/feed.json, 4-final/summaries.json
Output: enriched 4-final/feed.json (in-place)
"""

from __future__ import annotations

import json
import os
import re
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse

DATA = Path(__file__).resolve().parent.parent
FEED_PATH = DATA / "4-final" / "feed.json"
DIGEST_PATH = DATA / "4-final" / "digest.json"
SUMMARIES_PATH = DATA / "4-final" / "summaries.json"
HISTORY_DIR = DATA / "5-history"

STOP = {
    "the", "a", "an", "is", "are", "was", "were", "be", "been", "being",
    "have", "has", "had", "do", "does", "did", "will", "would", "could",
    "should", "may", "might", "can", "shall", "to", "of", "in", "for",
    "on", "with", "at", "by", "from", "as", "into", "through", "during",
    "before", "after", "above", "below", "between", "out", "off", "over",
    "under", "again", "further", "then", "once", "here", "there", "when",
    "where", "why", "how", "all", "both", "each", "few", "more", "most",
    "other", "some", "such", "no", "nor", "not", "only", "own", "same",
    "so", "than", "too", "very", "just", "because", "but", "and", "or",
    "if", "while", "about", "up", "its", "it", "that", "this", "what",
    "which", "who", "whom", "new", "your", "you", "we", "they", "them",
    "our", "his", "her", "he", "she", "my", "me", "i",
}

GENERIC = {
    "show", "open", "source", "code", "skills", "fable", "using", "make",
    "want", "need", "best", "top", "get", "set", "run", "use", "way",
    "day", "year", "time", "world", "people", "things", "work", "like",
    "just", "still", "even", "also", "much", "many", "good", "great",
    "first", "last", "long", "high", "old", "big", "small", "right",
    "free", "full", "real", "true", "false", "simple", "easy", "hard",
    "build", "built", "building", "learn", "start", "help", "take", "find", "think", "look",
    "come", "give", "back", "down", "well", "part", "made", "read",
    "post", "ask", "say", "tell", "see", "know", "try", "keep",
    "site", "app", "tool", "data", "file", "type", "line", "user", "users",
    # Expanded noise words that don't help discovery
    "one", "two", "three", "new", "now", "then", "here", "there", "this", "that",
    "these", "those", "some", "any", "every", "all", "each", "own", "self",
    "other", "another", "same", "different", "such", "only", "even", "still",
    "already", "yet", "always", "never", "often", "sometimes", "usually",
    "really", "actually", "probably", "definitely", "absolutely", "completely",
    "quite", "very", "too", "so", "more", "most", "less", "least", "much", "many",
    "little", "few", "lot", "bit", "plenty", "enough", "several", "various",
    "certain", "specific", "particular", "general", "common", "popular",
    "recent", "latest", "current", "modern", "future", "past", "former",
    "potential", "possible", "likely", "available", "accessible",
    "able", "unable", "ready", "willing", "likely", "unlikely",
    "different", "similar", "various", "several", "multiple", "single",
    "various", "diverse", "range", "series", "variety", "collection",
    "group", "set", "list", "array", "number", "amount", "quantity",
    "level", "degree", "kind", "sort", "type", "form", "version", "edition",
    "way", "means", "method", "approach", "process", "system", "platform",
    "framework", "model", "architecture", "structure", "format", "pattern",
    "example", "sample", "instance", "case", "point", "aspect", "part",
    "piece", "section", "area", "field", "space", "place", "region",
    "side", "end", "beginning", "start", "origin", "source", "origin",
    "result", "effect", "impact", "outcome", "output", "product", "produce",
    "issue", "problem", "question", "matter", "subject", "topic", "theme",
    "idea", "concept", "notion", "thought", "view", "opinion", "perspective",
    "article", "post", "story", "report", "update", "news", "blog", "video",
    "discussion", "comment", "thread", "tweet", "twitter", "website", "page",
    "link", "url", "site", "web", "webpage", "resource", "reference",
    "today", "yesterday", "tomorrow", "week", "month", "year", "day",
    "daily", "weekly", "monthly", "yearly", "hour", "minute", "second",
    "morning", "afternoon", "evening", "night",
}

TECH_KEYWORDS = {
    "ai", "llm", "gpt", "claude", "gemini", "deepseek", "qwen", "llama",
    "python", "rust", "go", "golang", "javascript", "typescript", "react", "vue",
    "docker", "kubernetes", "linux", "git", "github", "api", "sdk",
    "machine learning", "deep learning", "neural", "transformer",
    "openai", "anthropic", "google", "meta", "microsoft", "apple",
    "芯片", "大模型", "开源", "编程", "算法", "数据", "框架",
    "前端", "后端", "全栈", "微服务", "云原生", "容器", "部署",
    "agent", "rag", "embedding", "fine-tune", "inference", "training",
    "benchmark", "性能", "优化", "安全", "隐私", "区块链",
    "startup", "融资", "收购", "产品", "设计", "用户体验",
    "cursor", "codex", "copilot", "vibe coding",
}

# --- 标签匹配规则 ---
# ASCII 技术词按整词匹配（避免 "ai" 命中 "sailing"、"go" 命中 "google"），
# CJK 技术词按子串匹配。多词技术词在标签里是连字符形式（"machine-learning"），
# 频率裁剪时需用归一化后的集合判断（否则 "machine learning" 永不会命中）。
_CN_CHAR_RE = re.compile(r"[\u4e00-\u9fff]")
_TECH_ASCII_PATTERNS = [
    (kw, re.compile(r"(?<![a-z0-9])" + re.escape(kw) + r"(?![a-z0-9])"))
    for kw in TECH_KEYWORDS if not _CN_CHAR_RE.search(kw)
]
_TECH_CJK = [kw for kw in TECH_KEYWORDS if _CN_CHAR_RE.search(kw)]
TECH_TAGS = {kw.replace(" ", "-") for kw in TECH_KEYWORDS}

# 中文滑窗碎词过滤（与 build_trends.py 同源规则）
CN_FUNC_CHARS = set(
    "的了和是我你他她它们在就不都也还与及或被把让呢吗吧啊嘛么"
    "之其于以而且若因又再才只却并将能可要想说等该此哪谁什怎没有着过得地"
)
CN_JUNK_SUBSTR = ("如何", "为什么")
CN_STOP_PHRASES = {
    "这个", "那个", "什么", "怎么", "可以", "不是", "没有", "已经", "因为",
    "所以", "但是", "如果", "虽然", "知道", "觉得", "可能", "应该", "现在",
    "今天", "明天", "昨天", "大家", "自己", "问题", "东西", "事情", "怎么样",
    "为什么", "这么", "那么", "还是", "就是", "这些", "那些", "一种", "一个",
    "看待", "带来", "个月", "推出", "上线", "发布", "宣布", "据悉",
    "开始", "近日", "最近", "最新", "公司", "行业", "全面", "分享", "半年",
    "时代", "多少",
}
_CJK_RUN_RE = re.compile(r"[\u4e00-\u9fff]+")


def _cjk_tag_ok(gram: str) -> bool:
    """中文标签合法性：非停用短语、无疑问前缀、不含虚字。"""
    if gram in CN_STOP_PHRASES:
        return False
    if any(j in gram for j in CN_JUNK_SUBSTR):
        return False
    return not any(c in CN_FUNC_CHARS for c in gram)

# Tags that are too generic or noisy to be useful
TAG_DENYLIST = {
    "blog", "article", "news", "post", "story", "video", "discussion",
    "comments", "twitter", "thread", "website", "page", "link", "update",
    "announcing", "announced", "announces", "launch", "launches", "launched",
    "introducing", "introduction", "review", "reviews", "guide", "guides",
    "tutorial", "tutorials", "weekly", "monthly", "daily", "today", "yesterday",
    "new", "latest", "top", "best", "good", "great", "big", "small", "old",
    "year", "years", "month", "months", "day", "days", "week", "weeks",
    "2025", "2026", "2027",
    # News sites / domains that leak through as tags
    "bbc", "reuters", "theguardian", "guardian", "nytimes", "wsj", "economist",
    "arstechnica", "techcrunch", "bloomberg", "theatlantic", "theregister",
    "cnbc", "ft", "washingtonpost", "apnews", "aljazeera", "wired",
    # Generic web/platform words
    "com", "org", "io", "net", "co", "app", "web", "online", "internet",
    "digital", "virtual", "remote", "local", "global", "public", "private",
    "internal", "external", "official", "unofficial", "main", "primary",
    "secondary", "final", "initial", "original", "basic", "advanced",
    "beginner", "intermediate", "expert", "professional", "amateur",
    # Verbs / actions that don't tag well
    "built", "building", "make", "making", "made", "create", "creating",
    "created", "write", "writing", "written", "read", "reading",
    "run", "running", "use", "using", "used", "get", "getting", "got",
    "take", "taking", "took", "give", "giving", "gave",
    "find", "finding", "found", "search", "searching",
    "build", "learn", "start", "help", "think", "look", "come", "back",
    "down", "well", "ask", "say", "tell", "see", "know", "try", "keep",
    "without", "against", "behind", "between", "among", "within", "beyond",
    "above", "below", "under", "over", "across", "through", "into", "onto",
    # Common generic nouns
    "system", "computer", "server", "machine", "device", "hardware",
    "software", "program", "application", "browser", "engine", "network",
    "database", "storage", "memory", "chip", "cpu", "gpu", "screen",
    "phone", "mobile", "desktop", "laptop", "tablet", "watch",
    "company", "startup", "business", "industry", "market", "economy",
    "government", "organization", "institution", "university", "school",
    "team", "group", "people", "person", "user", "customer", "client",
    "developer", "engineer", "researcher", "scientist", "founder", "ceo",
    "executive", "leader", "manager", "employee", "worker",
    "study", "research", "paper", "report", "analysis", "survey",
    "test", "testing", "benchmark", "evaluation", "assessment",
    "performance", "speed", "fast", "faster", "slow", "slower",
    "security", "privacy", "safety", "risk", "threat", "attack",
    "cost", "price", "value", "money", "fund", "investment", "revenue",
    "profit", "loss", "sale", "deal", "contract", "agreement",
    # Content quality / length artifacts
    "en", "english", "chinese", "zh", "cn",
    # Additional noisy generic words surfaced by frequency analysis
    "window", "windows", "language", "game", "gaming", "control", "controls",
    "tech", "technology", "human", "humans", "native", "natives", "zero",
    "project", "projects", "based", "supported", "support", "supports",
    "live", "living", "life", "home", "house", "book", "books", "art", "arts",
    "rule", "rules", "map", "maps", "smart", "brain", "power", "stop",
    "service", "services", "task", "tasks", "job", "jobs", "age", "ages",
    "alternative", "alternatives", "hosted", "hosting", "skill", "skills",
    "history", "historical", "their", "there", "then", "than", "says", "said",
    "don", "doesn", "isn", "wasn", "weren", "haven", "hasn", "hadn", "couldn",
    "wouldn", "shouldn", "mightn", "mustn", "needn", "daren", "oughtn", "shan",
    "development", "developments", "harness", "harnessing", "turn", "turns",
    "science", "scientific", "engineering", "engineer", "engineers",
    "design", "designs", "image", "images", "pdf", "pdfs", "token", "tokens",
    "data", "datum", "chip", "chips", "programming", "programmer", "programmers",
    "coding", "coder", "coders", "computer", "computers", "server", "servers",

    # Time / state
    "now", "then", "soon", "later", "recently", "currently", "finally",
    "already", "yet", "still", "just", "only", "even",
}

# Simple singular forms for common plurals
PLURAL_MAP = {
    "llms": "llm",
    "agents": "agent",
    "apis": "api",
    "sdks": "sdk",
    "frameworks": "framework",
    "libraries": "library",
    "tools": "tool",
    "apps": "app",
    "services": "service",
    "platforms": "platform",
    "models": "model",
    "systems": "system",
    "networks": "network",
    "databases": "database",
    "languages": "language",
    "projects": "project",
    "companies": "company",
    "startups": "startup",
    "products": "product",
    "games": "game",
    "users": "user",
    "developers": "developer",
    "engineers": "engineer",
    "researchers": "researcher",
    "founders": "founder",
    "investors": "investor",
    "customers": "customer",
    "clients": "client",
    "partners": "partner",
    "employees": "employee",
    "members": "member",
    "communities": "community",
    "countries": "country",
    "cities": "city",
    "markets": "market",
    "industries": "industry",
    "technologies": "technology",
    "techniques": "technique",
    "methods": "method",
    "approaches": "approach",
    "processes": "process",
    "features": "feature",
    "functions": "function",
    "components": "component",
    "modules": "module",
    "packages": "package",
    "versions": "version",
    "updates": "update",
    "releases": "release",
    "announcements": "announcement",
    "improvements": "improvement",
    "enhancements": "enhancement",
    "changes": "change",
    "fixes": "fix",
    "bugs": "bug",
    "issues": "issue",
    "questions": "question",
    "answers": "answer",
    "comments": "comment",
    "discussions": "discussion",
    "conversations": "conversation",
    "interviews": "interview",
    "talks": "talk",
    "presentations": "presentation",
    "videos": "video",
    "podcasts": "podcast",
    "articles": "article",
    "posts": "post",
    "stories": "story",
    "essays": "essay",
    "guides": "guide",
    "tutorials": "tutorial",
    "docs": "doc",
    "documents": "document",
    "reports": "report",
    "papers": "paper",
    "studies": "study",
    "analyses": "analysis",
    "reviews": "review",
    "summaries": "summary",
    "notes": "note",
    "examples": "example",
    "samples": "sample",
    "demos": "demo",
    "prototypes": "prototype",
    "experiments": "experiment",
    "benchmarks": "benchmark",
    "tests": "test",
    "evaluations": "evaluation",
    "comparisons": "comparison",
    "alternatives": "alternative",
    "options": "option",
    "choices": "choice",
    "solutions": "solution",
    "ideas": "idea",
    "concepts": "concept",
    "theories": "theory",
    "hypotheses": "hypothesis",
    "predictions": "prediction",
    "expectations": "expectation",
    "goals": "goal",
    "objectives": "objective",
    "targets": "target",
    "milestones": "milestone",
    "achievements": "achievement",
    "successes": "success",
    "failures": "failure",
    "challenges": "challenge",
    "problems": "problem",
    "obstacles": "obstacle",
    "barriers": "barrier",
    "limitations": "limitation",
    "constraints": "constraint",
    "restrictions": "restriction",
    "requirements": "requirement",
    "specifications": "specification",
    "standards": "standard",
    "guidelines": "guideline",
    "principles": "principle",
    "practices": "practice",
    "patterns": "pattern",
    "strategies": "strategy",
    "tactics": "tactic",
    "plans": "plan",
    "roadmaps": "roadmap",
    "schedules": "schedule",
    "timelines": "timeline",
    "deadlines": "deadline",
    "priorities": "priority",
    "tasks": "task",
    "activities": "activity",
    "operations": "operation",
    "workflows": "workflow",
    "procedures": "procedure",
    "policies": "policy",
    "rules": "rule",
    "regulations": "regulation",
    "laws": "law",
    "rights": "right",
    "responsibilities": "responsibility",
    "roles": "role",
    "positions": "position",
    "jobs": "job",
    "careers": "career",
    "professions": "profession",
    "skills": "skill",
    "abilities": "ability",
    "talents": "talent",
    "expertises": "expertise",
    "experiences": "experience",
    "backgrounds": "background",
    "qualifications": "qualification",
    "credentials": "credential",
    "certifications": "certification",
    "degrees": "degree",
    "diplomas": "diploma",
    "licenses": "license",
    "permits": "permit",
    "approvals": "approval",
    "authorizations": "authorization",
    "permissions": "permission",
    "consents": "consent",
    "agreements": "agreement",
    "contracts": "contract",
    "deals": "deal",
    "transactions": "transaction",
    "exchanges": "exchange",
    "transfers": "transfer",
    "payments": "payment",
    "purchases": "purchase",
    "sales": "sale",
    "orders": "order",
    "deliveries": "delivery",
    "shipments": "shipment",
    "logistics": "logistic",
    "supplies": "supply",
    "inventories": "inventory",
    "stocks": "stock",
    "assets": "asset",
    "resources": "resource",
    "materials": "material",
    "ingredients": "ingredient",
    "parts": "part",
    "pieces": "piece",
    "units": "unit",
    "items": "item",
    "goods": "good",
    "commodities": "commodity",
    "merchandises": "merchandise",
    "brands": "brand",
    "labels": "label",
    "logos": "logo",
    "trademarks": "trademark",
    "names": "name",
    "titles": "title",
    "headlines": "headline",
    "subtitles": "subtitle",
    "descriptions": "description",
    "abstracts": "abstract",
    "introductions": "introduction",
    "conclusions": "conclusion",
    "results": "result",
    "findings": "finding",
    "discoveries": "discovery",
    "inventions": "invention",
    "innovations": "innovation",
    "creations": "creation",
    "designs": "design",
    "styles": "style",
    "formats": "format",
    "layouts": "layout",
    "structures": "structure",
    "architectures": "architecture",
    "infrastructures": "infrastructure",
    "environments": "environment",
    "ecosystems": "ecosystem",
    "contexts": "context",
    "settings": "setting",
    "configurations": "configuration",
    "preferences": "preference",
    "properties": "property",
    "attributes": "attribute",
    "characteristics": "characteristic",
    "qualities": "quality",
    "traits": "trait",
    "aspects": "aspect",
    "facets": "facet",
    "dimensions": "dimension",
    "factors": "factor",
    "variables": "variable",
    "parameters": "parameter",
    "metrics": "metric",
    "indicators": "indicator",
    "measures": "measure",
    "measurements": "measurement",
    "values": "value",
    "numbers": "number",
    "figures": "figure",
    "statistics": "statistic",
    "data": "data",
    "datasets": "dataset",
    "repositories": "repository",
    "archives": "archive",
    "records": "record",
    "logs": "log",
    "files": "file",
    "folders": "folder",
    "directories": "directory",
    "paths": "path",
    "routes": "route",
    "urls": "url",
    "links": "link",
    "connections": "connection",
    "relationships": "relationship",
    "associations": "association",
    "correlations": "correlation",
    "dependencies": "dependency",
    "dependents": "dependent",
    "children": "child",
    "parents": "parent",
    "siblings": "sibling",
    "roots": "root",
    "branches": "branch",
    "leaves": "leaf",
    "nodes": "node",
    "edges": "edge",
    "graphs": "graph",
    "trees": "tree",
    "charts": "chart",
    "diagrams": "diagram",
    "maps": "map",
    "images": "image",
    "pictures": "picture",
    "photos": "photo",
    "graphics": "graphic",
    "illustrations": "illustration",
    "icons": "icon",
    "symbols": "symbol",
    "emojis": "emoji",
    "characters": "character",
    "letters": "letter",
    "words": "word",
    "phrases": "phrase",
    "sentences": "sentence",
    "paragraphs": "paragraph",
    "chapters": "chapter",
    "sections": "section",
    "pages": "page",
    "books": "book",
    "novels": "novel",
    "publications": "publication",
    "journals": "journal",
    "magazines": "magazine",
    "newspapers": "newspaper",
    "periodicals": "periodical",
    "newsletters": "newsletter",
    "feeds": "feed",
    "channels": "channel",
    "stations": "station",
    "broadcasts": "broadcast",
    "streams": "stream",
    "episodes": "episode",
    "series": "series",
    "seasons": "season",
    "events": "event",
    "conferences": "conference",
    "meetups": "meetup",
    "workshops": "workshop",
    "seminars": "seminar",
    "webinars": "webinar",
    "courses": "course",
    "classes": "class",
    "lessons": "lesson",
    "lectures": "lecture",
    "trainings": "training",
    "programs": "program",
    "curricula": "curriculum",
    "syllabi": "syllabus",
    "assignments": "assignment",
    "homeworks": "homework",
    "theses": "thesis",
    "dissertations": "dissertation",
    "portfolios": "portfolio",
    "showcases": "showcase",
    "galleries": "gallery",
    "exhibitions": "exhibition",
    "performances": "performance",
    "concerts": "concert",
    "shows": "show",
    "competitions": "competition",
    "contests": "contest",
    "tournaments": "tournament",
    "matches": "match",
    "sports": "sport",
    "races": "race",
    "marathons": "marathon",
    "triathlons": "triathlon",
    "olympics": "olympic",
    "championships": "championship",
    "leagues": "league",
    "divisions": "division",
    "teams": "team",
    "clubs": "club",
    "organizations": "organization",
    "institutions": "institution",
    "foundations": "foundation",
    "societies": "society",
    "unions": "union",
    "alliances": "alliance",
    "coalitions": "coalition",
    "movements": "movement",
    "campaigns": "campaign",
    "drives": "drive",
    "initiatives": "initiative",
    "efforts": "effort",
    "attempts": "attempt",
    "tries": "try",
    "endeavors": "endeavor",
    "ventures": "venture",
    "enterprises": "enterprise",
    "businesses": "business",
    "corporations": "corporation",
    "incorporations": "incorporation",
    "firms": "firm",
    "agencies": "agency",
    "bureaus": "bureau",
    "departments": "department",
    "offices": "office",
    "sectors": "sector",
    "segments": "segment",
    "niches": "niche",
    "economies": "economy",
    "landscapes": "landscape",
    "climates": "climate",
    "conditions": "condition",
    "situations": "situation",
    "scenarios": "scenario",
    "cases": "case",
    "instances": "instance",
    "demonstrations": "demonstration",
    "proofs": "proof",
    "evidences": "evidence",
    "facts": "fact",
    "details": "detail",
    "particulars": "particular",
    "specifics": "specific",
    "nuances": "nuance",
    "subtleties": "subtlety",
    "complexities": "complexity",
    "complications": "complication",
    "difficulties": "difficulty",
    "hurdles": "hurdle",
    "matters": "matter",
    "concerns": "concern",
    "worries": "worry",
    "anxieties": "anxiety",
    "fears": "fear",
    "risks": "risk",
    "dangers": "danger",
    "threats": "threat",
    "hazards": "hazard",
    "vulnerabilities": "vulnerability",
    "weaknesses": "weakness",
    "strengths": "strength",
    "advantages": "advantage",
    "benefits": "benefit",
    "gains": "gain",
    "profits": "profit",
    "rewards": "reward",
    "returns": "return",
    "yields": "yield",
    "outputs": "output",
    "outcomes": "outcome",
    "consequences": "consequence",
    "effects": "effect",
    "impacts": "impact",
    "influences": "influence",
    "implications": "implication",
    "repercussions": "repercussion",
    "ramifications": "ramification",
    "aftermaths": "aftermath",
    "fallouts": "fallout",
    "side-effects": "side-effect",
    "byproducts": "byproduct",
    "spinoffs": "spinoff",
    "derivatives": "derivative",
    "variations": "variation",
    "editions": "edition",
    "iterations": "iteration",
    "generations": "generation",
    "revolutions": "revolution",
    "evolutions": "evolution",
    "progressions": "progression",
    "developments": "development",
    "advances": "advance",
    "breakthroughs": "breakthrough",
    "productions": "production",
    "works": "work",
    "duties": "duty",
    "purposes": "purpose",
    "uses": "use",
    "applications": "application",
    "usages": "usage",
    "utilities": "utility",
    "capabilities": "capability",
    "capacities": "capacity",
    "powers": "power",
    "forces": "force",
    "energies": "energy",
    "intensities": "intensity",
    "magnitudes": "magnitude",
    "scales": "scale",
    "sizes": "size",
    "volumes": "volume",
    "quantities": "quantity",
    "amounts": "amount",
    "counts": "count",
    "totals": "total",
    "sums": "sum",
    "aggregates": "aggregate",
    "averages": "average",
    "means": "mean",
    "medians": "median",
    "modes": "mode",
    "ranges": "range",
    "minimums": "minimum",
    "maximums": "maximum",
    "extremes": "extreme",
    "limits": "limit",
    "boundaries": "boundary",
    "borders": "border",
    "margins": "margin",
    "thresholds": "threshold",
    "ceilings": "ceiling",
    "floors": "floor",
    "walls": "wall",
    "gates": "gate",
    "doors": "door",
    "windows": "window",
    "openings": "opening",
    "entrances": "entrance",
    "exits": "exit",
    "passages": "passage",
    "ways": "way",
    "directions": "direction",
    "destinations": "destination",
    "locations": "location",
    "places": "place",
    "points": "point",
    "spots": "spot",
    "sites": "site",
    "areas": "area",
    "regions": "region",
    "zones": "zone",
    "territories": "territory",
    "districts": "district",
    "neighborhoods": "neighborhood",
    "quarters": "quarter",
    "portions": "portion",
    "shares": "share",
    "fractions": "fraction",
    "percentages": "percentage",
    "ratios": "ratio",
    "proportions": "proportion",
    "rates": "rate",
    "speeds": "speed",
    "velocities": "velocity",
    "paces": "pace",
    "tempos": "tempo",
    "rhythms": "rhythm",
    "frequencies": "frequency",
    "periods": "period",
    "durations": "duration",
    "intervals": "interval",
    "gaps": "gap",
    "spaces": "space",
    "distances": "distance",
    "lengths": "length",
    "widths": "width",
    "heights": "height",
    "depths": "depth",
    "breadths": "breadth",
    "spans": "span",
    "extents": "extent",
    "levels": "level",
    "layers": "layer",
    "tiers": "tier",
    "ranks": "rank",
    "grades": "grade",
    "categories": "category",
    "classifications": "classification",
    "taxonomies": "taxonomy",
    "hierarchies": "hierarchy",
    "families": "family",
    "genera": "genus",
    "species": "species",
    "types": "type",
    "kinds": "kind",
    "sorts": "sort",
    "forms": "form",
    "shapes": "shape",
    "molds": "mold",
    "templates": "template",
    "stencils": "stencil",
    "mockups": "mockup",
    "wireframes": "wireframe",
    "sketches": "sketch",
    "drafts": "draft",
    "outlines": "outline",
    "blueprints": "blueprint",
    "schematics": "schematic",
    "plots": "plot",
    "tables": "table",
    "matrices": "matrix",
    "grids": "grid",
    "lists": "list",
    "arrays": "array",
    "queues": "queue",
    "stacks": "stack",
    "heaps": "heap",
    "webs": "web",
    "meshes": "mesh",
    "topologies": "topology",
    "arrangements": "arrangement",
    "compositions": "composition",
    "constitutions": "constitution",
    "makeups": "makeup",
    "formations": "formation",
    "alignments": "alignment",
    "orientations": "orientation",
    "placements": "placement",
    "dispositions": "disposition",
    "distributions": "distribution",
    "allocations": "allocation",
    "designations": "designation",
    "appointments": "appointment",
    "nominations": "nomination",
    "selections": "selection",
    "picks": "pick",
    "substitutes": "substitute",
    "replacements": "replacement",
    "successors": "successor",
    "predecessors": "predecessor",
    "ancestors": "ancestor",
    "descendants": "descendant",
    "relatives": "relative",
    "relations": "relation",
    "bonds": "bond",
    "ties": "tie",
    "attachments": "attachment",
    "affiliations": "affiliation",
    "partnerships": "partnership",
    "collaborations": "collaboration",
    "cooperations": "cooperation",
    "mergers": "merger",
    "acquisitions": "acquisition",
    "takeovers": "takeover",
    "buyouts": "buyout",
    "investments": "investment",
    "fundings": "funding",
    "financings": "financing",
    "loans": "loan",
    "credits": "credit",
    "debts": "debt",
    "liabilities": "liability",
    "holdings": "holding",
    "real-estates": "real-estate",
    "estates": "estate",
    "wealths": "wealth",
    "fortunes": "fortune",
    "riches": "rich",
    "treasures": "treasure",
    "valuables": "valuable",
    "wares": "ware",
    "provisions": "provision",
    "rations": "ration",
    "stakes": "stake",
    "interests": "interest",
    "equities": "equity",
    "securities": "security",
    "futures": "future",
    "swaps": "swap",
    "hedges": "hedge",
    "bets": "bet",
    "wagers": "wager",
    "gamble": "gamble",
    "speculations": "speculation",
    "gambles": "gamble",
    "chances": "chance",
    "opportunities": "opportunity",
    "prospects": "prospect",
    "possibilities": "possibility",
    "potentials": "potential",
    "competencies": "competency",
    "gifts": "gift",
    "specializations": "specialization",
    "concentrations": "concentration",
    "focuses": "focus",
    "emphases": "emphasis",
    "inclinations": "inclination",
    "tendencies": "tendency",
    "trends": "trend",
    "cycles": "cycle",
    "phases": "phase",
    "stages": "stage",
    "steps": "step",
    "ratings": "rating",
    "scores": "score",
    "marks": "mark",
    "assessments": "assessment",
    "appraisals": "appraisal",
    "judgments": "judgment",
    "opinions": "opinion",
    "views": "view",
    "perspectives": "perspective",
    "standpoints": "standpoint",
    "viewpoints": "viewpoint",
    "angles": "angle",
    "slants": "slant",
    "biases": "bias",
    "prejudices": "prejudice",
    "leanings": "leaning",
    "tastes": "taste",
    "flavors": "flavor",
    "varieties": "variety",
    "genres": "genre",
    "breeds": "breed",
    "strains": "strain",
    "cultivars": "cultivar",
    "cultures": "culture",
    "traditions": "tradition",
    "customs": "custom",
    "habits": "habit",
    "routines": "routine",
    "rituals": "ritual",
    "ceremonies": "ceremony",
    "celebrations": "celebration",
    "festivals": "festival",
    "holidays": "holiday",
    "vacations": "vacation",
    "trips": "trip",
    "journeys": "journey",
    "travels": "travel",
    "tours": "tour",
    "voyages": "voyage",
    "expeditions": "expedition",
    "adventures": "adventure",
    "explorations": "exploration",
    "missions": "mission",
    "crusades": "crusade",
    "pushes": "push",
    "undertakings": "undertaking",
    "schemes": "scheme",
    "maneuvers": "maneuver",
    "moves": "move",
    "actions": "action",
    "acts": "act",
    "deeds": "deed",
    "feats": "feat",
    "accomplishments": "accomplishment",
    "victories": "victory",
    "triumphs": "triumph",
    "wins": "win",
    "progresses": "progress",
    "headways": "headway",
    "strides": "stride",
    "leaps": "leap",
    "jumps": "jump",
    "bounds": "bound",
}

# Canonical forms for near-duplicate tags
TAG_SYNONYMS = {
    "github-trending": "github",
    "product-hunt": "producthunt",
    "artificial-intelligence": "ai",
    "machine-learning": "machine-learning",
    "large-language-model": "llm",
    "large-language-models": "llm",
    "llms": "llm",
    "open-ai": "openai",
    "chatgpt": "chatgpt",
    "chat-gpt": "chatgpt",
    "anthropic-claude": "claude",
    "google-gemini": "gemini",
    "msft": "microsoft",
    "ms": "microsoft",
    "golang": "go",
    "js": "javascript",
    "ts": "typescript",
    "reactjs": "react",
    "vuejs": "vue",
    "k8s": "kubernetes",
    "container": "docker",
    "containers": "docker",
}


def extract_domain(url: str) -> str:
    try:
        host = urlparse(url).hostname or ""
        # 只剥离前缀 www.，不能 replace 删除所有出现处（中间域名段也会被误删）
        return host.lower().removeprefix("www.")
    except Exception:
        return ""


def domain_tag(domain: str) -> str:
    """Map known domains to a concise tag; ignore unknown domains to avoid noise."""
    mapping = {
        "github.com": "github",
        "news.ycombinator.com": "hackernews",
        "producthunt.com": "producthunt",
        "36kr.com": "36kr",
        "juejin.cn": "juejin",
        "zhihu.com": "zhihu",
        "infoq.cn": "infoq",
        "twitter.com": "twitter",
        "x.com": "twitter",
        "arxiv.org": "arxiv",
        "youtube.com": "youtube",
    }
    return mapping.get(domain, "")


def extract_keywords(title: str, description: str = "") -> list[str]:
    """Extract tags from title+description.

    英文技术词整词匹配；中文连续段内长 gram 优先滑窗（"正式版发布" 整体
    成词，而不是 "正式版发" 之类残缺窗口），并过滤虚字/疑问前缀/停用短语。
    返回排序后的去重列表（输出确定性，避免每次运行 diff 噪音）。
    """
    text = f"{title} {description}".lower()
    keywords: set[str] = set()

    # 1) 技术词表：ASCII 整词匹配，CJK 子串匹配
    for kw, pat in _TECH_ASCII_PATTERNS:
        if pat.search(text):
            keywords.add(kw)
    for kw in _TECH_CJK:
        if kw in text:
            keywords.add(kw)

    # 2) 英文词（≥3 字母，非停用词/泛用词）
    for w in re.findall(r"[a-zA-Z]{3,}", text):
        wl = w.lower()
        if wl not in STOP and wl not in GENERIC:
            keywords.add(wl)

    # 3) 中文：连续汉字段优先整体成词（≤12 字），避免 "正式版发" 之类
    #    残缺滑窗碎片；疑问句式（含 如何/为什么）整段跳过；超长段退回
    #    长 gram 优先滑窗 + 覆盖率去重
    for run in _CJK_RUN_RE.findall(text):
        if len(run) < 2:
            continue
        if any(j in run for j in CN_JUNK_SUBSTR):
            continue  # 疑问句式（"如何看待…"）不产标签
        if len(run) <= 12:
            if _cjk_tag_ok(run):
                keywords.add(run)
            continue
        accepted: list[str] = []
        for n in range(min(len(run), 6), 1, -1):
            for i in range(len(run) - n + 1):
                gram = run[i:i + n]
                if any(gram in a for a in accepted):
                    continue  # 已被更长 gram 覆盖的碎片
                if not _cjk_tag_ok(gram):
                    continue
                accepted.append(gram)
        keywords.update(accepted)

    return sorted(keywords)


def parse_time(t):
    try:
        if isinstance(t, (int, float)) and t > 0:
            if t > 1e12:
                t = t / 1000
            return datetime.fromtimestamp(t, tz=timezone.utc)
        s = str(t)
        if s.isdigit():
            n = int(s)
            if n > 1e12:
                n = n / 1000
            return datetime.fromtimestamp(n, tz=timezone.utc)
        dt = datetime.fromisoformat(s.replace("Z", "+00:00"))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt
    except Exception:
        return None


def compute_quality_score(item: dict, has_summary: bool, max_score: float, max_comments: float) -> float:
    """Compute a 0-100 quality score combining engagement, recency and enrichment."""
    score = item.get("score", 0)
    comments = item.get("comments", 0)

    score_norm = (score / max_score * 100) if max_score > 0 else 0
    comments_norm = (comments / max_comments * 100) if max_comments > 0 else 0

    # Recency: items from last 7 days get a boost
    dt = parse_time(item.get("time", ""))
    now = datetime.now(timezone.utc)
    recency = 0.0
    if dt:
        days_old = (now - dt).days
        if days_old <= 1:
            recency = 30
        elif days_old <= 7:
            recency = 15
        elif days_old <= 30:
            recency = 5

    summary_bonus = 10 if has_summary else 0

    # Combine: engagement average + recency + summary bonus
    quality = (score_norm * 0.35 + comments_norm * 0.35 + recency + summary_bonus)
    return min(round(quality, 1), 100)


# 源/域级标签：所有同源条目共享，对"相关条目"匹配无信息量
# （此前作为桶成员让 find_related 退化为 O(n²) 且结果被同源条目主导）
SOURCE_TAGS = {
    "hackernews", "github-trending", "producthunt", "juejin", "zhihu",
    "36kr", "infoq", "v2ex", "general-hot",
    "github", "youtube", "arxiv", "twitter",
}


def _content_kws(item: dict) -> set[str]:
    """条目的内容关键词（排除源/域级标签），用于相关匹配。"""
    tags = set(item.get("tags", [])) - SOURCE_TAGS
    return tags | set(extract_keywords(item.get("title", ""), item.get("description", "")))


def build_inverted_index(all_items: list[dict]) -> dict[str, list[dict]]:
    """keyword -> list of items that contain it."""
    index: dict[str, list[dict]] = {}
    for item in all_items:
        for kw in _content_kws(item):
            index.setdefault(kw, []).append(item)
    return index


def find_related(item: dict, inverted_index: dict[str, list[dict]], item_by_id: dict[str, dict], top_n: int = 5) -> list[str]:
    """Find related items by keyword overlap using an inverted index.

    源/域级标签不参与匹配（排除后桶成员数量级下降，且结果不再被
    "同源其他条目"主导），也不做同源加分——跨源相关性才是目标。
    """
    item_kws = _content_kws(item)
    if not item_kws:
        return []

    candidate_scores: dict[str, float] = {}

    for kw in item_kws:
        for other in inverted_index.get(kw, []):
            if other["id"] == item["id"]:
                continue
            candidate_scores[other["id"]] = candidate_scores.get(other["id"], 0) + 1

    scored = []
    for other_id, overlap in candidate_scores.items():
        other = item_by_id.get(other_id)
        if not other:
            continue
        quality = other.get("quality_score", 50)
        scored.append((overlap * (quality / 100), other_id))

    scored.sort(key=lambda x: x[0], reverse=True)
    return [iid for _, iid in scored[:top_n]]


def _write_json_atomic(path: Path, obj) -> None:
    """写 JSON 到临时文件后原子替换，避免中途崩溃留下半写文件。"""
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_text(json.dumps(obj, indent=2, ensure_ascii=False), encoding="utf-8")
    os.replace(tmp, path)


def apply_enrichment_to_history(id_to_item: dict[str, dict], today_key: str):
    """把 enrich 结果（domain/quality_score/summary）回写到当日历史快照，
    让归档页"按质量排序"和 item 详情页有数据。"""
    snapshot_path = HISTORY_DIR / f"{today_key}.json"
    if not snapshot_path.exists():
        return
    try:
        data = json.loads(snapshot_path.read_text())
        updated = 0
        for section in ("items", "digest_items"):
            for item in data.get(section, []):
                enriched = id_to_item.get(item.get("id", ""))
                if not enriched:
                    continue
                item["domain"] = enriched.get("domain", "")
                item["quality_score"] = enriched.get("quality_score", 0)
                if enriched.get("summary_zh"):
                    item["summary_zh"] = enriched["summary_zh"]
                    item["summary_en"] = enriched.get("summary_en", "")
                updated += 1
        if updated:
            _write_json_atomic(snapshot_path, data)
            print(f"[Enrich] Updated {updated} items in history snapshot {snapshot_path.name}")
    except Exception as e:
        print(f"[WARN] Failed to update history snapshot: {e}", file=sys.stderr)


def main():
    if not FEED_PATH.exists():
        print("[Enrich] feed.json not found, skipping")
        return

    feed = json.loads(FEED_PATH.read_text())
    items = feed.get("items", [])
    if not items:
        # 空 feed（fetch 全挂但 aggregate 写出空结构）：直接跳过，
        # 避免后续除零崩溃留下半处理状态
        print("[Enrich] feed.json has no items, skipping")
        return

    summaries = {}
    if SUMMARIES_PATH.exists():
        summaries = json.loads(SUMMARIES_PATH.read_text())

    # 按来源分别取最大值做归一化，避免 GH 总星数（几十万）碾压 HN 分数（几百）
    max_by_source: dict[str, dict[str, float]] = {}
    for i in items:
        m = max_by_source.setdefault(i.get("source", ""), {"score": 0.0, "comments": 0.0})
        m["score"] = max(m["score"], i.get("score", 0))
        m["comments"] = max(m["comments"], i.get("comments", 0))

    # First pass: enrich each item
    for item in items:
        domain = extract_domain(item.get("url", ""))
        item["domain"] = domain
        dtag = domain_tag(domain)

        source = item.get("source", "")
        source_tag = source.replace("_", "-")

        keyword_tags = extract_keywords(item.get("title", ""), item.get("description", ""))

        existing_tags = set(t.lower() for t in item.get("tags", []) if t)
        # 清理历史遗留的中文碎词标签（如 "正式版发"、"如何评价"）：
        # 中文标签只保留本次提取认可、或 2-3 字且通过碎词过滤的（短词无法再拆）
        existing_tags = {
            t for t in existing_tags
            if not _CN_CHAR_RE.search(t)
            or t in keyword_tags
            or (len(t) < 4 and _cjk_tag_ok(t))
        }
        new_tags = {dtag, source_tag} | set(keyword_tags)
        # Merge and normalize: lowercase, hyphen-separated, deduped
        normalized = set()
        for t in (existing_tags | new_tags):
            if not t or len(t) < 2:
                continue
            t = re.sub(r"[\s_]+", "-", t).strip("-")
            if not t:
                continue
            # Apply plural -> singular mapping
            t = PLURAL_MAP.get(t, t)
            normalized.add(t)

        # Apply synonym mapping and remove stop / generic / denylisted tags
        canonical = {TAG_SYNONYMS.get(t, t) for t in normalized}
        merged = sorted(
            t for t in canonical
            if t not in STOP and t not in GENERIC and t not in TAG_DENYLIST
        )
        item["tags"] = merged

        has_summary = bool(summaries.get(item.get("id", ""), {}).get("summary_zh"))
        # 把 summaries.json 的摘要按 id 合并进 feed item，供详情页直接使用
        if has_summary:
            s = summaries[item["id"]]
            item["summary_zh"] = s.get("summary_zh", "")
            item["summary_en"] = s.get("summary_en", "")
        m = max_by_source.get(source, {})
        item["quality_score"] = compute_quality_score(
            item, has_summary, m.get("score", 0), m.get("comments", 0))

    # Second pass: prune rare noise tags globally
    MIN_TAG_FREQUENCY = 3
    tag_counts = Counter()
    for item in items:
        tag_counts.update(item.get("tags", []))
    keep_tags = {tag for tag, count in tag_counts.items()
                 if count >= MIN_TAG_FREQUENCY or tag in TECH_TAGS}
    for item in items:
        item["tags"] = [t for t in item.get("tags", []) if t in keep_tags]

    # Third pass: find related items
    id_to_item = {i["id"]: i for i in items}
    inverted_index = build_inverted_index(items)
    for item in items:
        related = find_related(item, inverted_index, id_to_item)
        item["related_ids"] = related

    _write_json_atomic(FEED_PATH, feed)

    # Also update digest.json daily items with enriched metadata
    today_key = ""
    if DIGEST_PATH.exists():
        digest = json.loads(DIGEST_PATH.read_text())
        today_key = digest.get("daily", {}).get("date", "")
        updated = 0
        for item in digest.get("daily", {}).get("items", []):
            enriched = id_to_item.get(item.get("id", ""))
            if enriched:
                item["domain"] = enriched.get("domain", "")
                item["tags"] = enriched.get("tags", [])
                item["quality_score"] = enriched.get("quality_score", 0)
                item["related_ids"] = enriched.get("related_ids", [])
                if enriched.get("summary_zh"):
                    item["summary_zh"] = enriched["summary_zh"]
                    item["summary_en"] = enriched.get("summary_en", "")
                updated += 1
        _write_json_atomic(DIGEST_PATH, digest)
        print(f"[Enrich] Updated {updated} items in digest.json")

    # 回写当日历史快照（aggregate 阶段已由 save_snapshot 写出）
    if today_key:
        apply_enrichment_to_history(id_to_item, today_key)

    # Report
    tag_counts = Counter()
    for item in items:
        tag_counts.update(item.get("tags", []))

    print(f"[Enrich] {len(items)} items enriched")
    print(f"[Enrich] {len(tag_counts)} unique tags, top: {tag_counts.most_common(10)}")
    print(f"[Enrich] avg quality score: {sum(i.get('quality_score', 0) for i in items) / len(items):.1f}")


if __name__ == "__main__":
    main()
