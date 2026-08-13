#!/usr/bin/env python3
from __future__ import annotations

"""Generate bilingual summaries for digest items.

Priority:
  1. Existing summaries in summaries.json (skip if already have)
  2. LLM API (if DEEPSEEK_API_KEY or OPENAI_API_KEY env var set)
  3. Template fallback (low quality, last resort)

每次运行还会扫描 summaries.json 里 summary_zh 为空的历史条目，
从 digest + 历史快照找回原始条目后重新入队（不删库，LLM 不可用时留空下轮再试）。
"""

import hashlib
import json
import os
import re
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone, timedelta
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
FINAL_DIR = BASE_DIR / "4-final"
HISTORY_DIR = BASE_DIR / "5-history"
SUMMARIES_PATH = FINAL_DIR / "summaries.json"

BATCH_SIZE = 5
RETRY_BATCH_SIZE = 3        # 重试轮用更小批次，降低截断概率
MAX_RETRY_EMPTY = 30        # 每轮最多回填的历史空摘要条数

# 模板摘要的中文前缀（用于识别低质量模板产物，重新入队 + 统计口径）
TEMPLATE_PREFIXES_ZH = (
    "HN 热门", "开源项目", "Product Hunt 热门", "掘金精选",
    "知乎热榜", "36氪热门", "InfoQ 精选", "V2EX 热议",
)

# LLM config from environment variables (never hardcoded)
LLM_PROVIDERS = [
    {
        "name": "deepseek",
        "base_url": "https://api.deepseek.com",
        "api_key_env": "DEEPSEEK_API_KEY",
        "api_key_file": ".deepseek_key",  # 本地开发用，仅该 provider 生效
        "model": "deepseek-v4-flash",
    },
    {
        "name": "openai",
        "base_url": "https://api.openai.com/v1",
        "api_key_env": "OPENAI_API_KEY",
        "model": "gpt-4o-mini",
    },
]

SYSTEM_PROMPT = (
    "You are a senior tech editor writing bilingual summaries for a developer "
    "news digest. 你的读者是一线开发者，看重事实密度，反感营销腔。"
    "Output ONLY valid JSON — no markdown fences, no commentary."
)

USER_PROMPT_TEMPLATE = """为下面每条资讯各写一条中文摘要 (summary_zh) 和一条英文摘要 (summary_en)。

要求：
1. summary_zh：2-3 句自然中文，60-120 字。第一句讲清它是什么（给出标题没有的具体事实，不要复述标题）；第二句说明为什么重要、亮点是什么、或适合什么人。
2. summary_en：2-3 sentences of natural English, 50-90 words, same structure — what it is (facts beyond the title), then why it matters or who should care.
3. 技术名词、产品名、公司名保留英文原文（如 Kubernetes、Transformer、Claude、GitHub），不要硬译。
4. 禁止：复述标题凑字数；堆砌形容词和夸张修辞（如"神器""白月光""颠覆""震撼"）；套话结尾（如"值得关注""未来可期"）；列表、编号、竖线 | —— 必须是连贯段落。
5. 两条摘要覆盖相同的关键事实，但语言各自地道，不是逐句互译。
6. 事实边界：摘要里出现的公司名、人名、产品名、数字、版本号必须来自该条的 title、desc 或正文（readme/content 字段），禁止引入这些输入都未提及的实体（例如标题只写 Codex 时不得自行加上 "Amazon"）。拿不准就不写。
7. title 之外没有任何正文素材的条目（desc、readme、content 均为空，如只有链接的 HN 帖）：禁止猜测正文内容。基于标题能确定的事实写 1-2 句，并明确说明"原文是链接，未提供更多细节"（英文："the linked page isn't summarized here; details beyond the title aren't available"）。有正文的条目以正文（readme/content）为准提炼事实（它比 desc 完整），desc 仅作补充。

Items:
{items}

Output a JSON object with this exact shape (include every item id exactly once):
{{"summaries": [{{"id": "xxx", "summary_zh": "...", "summary_en": "..."}}, ...]}}"""


class LLMAuthError(Exception):
    """LLM API 认证失败（401/403）：key 无效，继续重试只会空耗时间。"""


def call_llm(base_url: str, api_key: str, model: str, prompt: str) -> str:
    """Call LLM API, return response text or empty string.

    401/403 立即抛 LLMAuthError（key 无效，全量重试无意义）；
    429/5xx 指数退避重试（1s/2s/4s）；连接失败重试一次后降级。
    """
    url = f"{base_url}/chat/completions"
    body = json.dumps({
        "model": model,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ],
        "temperature": 0.3,
        # reasoning 模型会消耗大量隐藏 token，5 条批量需要充足余量避免截断
        "max_tokens": 12000,
        "response_format": {"type": "json_object"},
    }).encode()

    req = urllib.request.Request(url, data=body, headers={
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}",
    })

    last_err: Exception | None = None
    for attempt in range(3):
        try:
            with urllib.request.urlopen(req, timeout=120) as resp:
                data = json.loads(resp.read().decode())
                choice = data["choices"][0]
                if choice.get("finish_reason") == "length":
                    print("  [WARN] LLM response truncated (finish_reason=length)", file=sys.stderr)
                return choice["message"]["content"].strip()
        except urllib.error.HTTPError as e:
            code = e.code
            if code in (401, 403):
                raise LLMAuthError(f"LLM auth failed (HTTP {code})") from e
            if code == 429 or code >= 500:
                wait = 2 ** attempt  # 1s / 2s / 4s
                print(f"  [WARN] LLM HTTP {code}, retry in {wait}s...", file=sys.stderr)
                last_err = e
                time.sleep(wait)
                continue
            print(f"  [WARN] LLM HTTP {code}: {e}", file=sys.stderr)
            return ""
        except Exception as e:
            last_err = e
            if attempt < 2:
                time.sleep(2 ** attempt)
                continue
    print(f"  [WARN] LLM call failed: {last_err}", file=sys.stderr)
    return ""


def build_prompt(items: list[dict]) -> str:
    """Build summarization prompt for a batch of items."""
    lines = []
    for i, item in enumerate(items):
        desc = (item.get("description") or "").strip()[:200] or "（无）"
        line = f"{i+1}. id={item['id']} | source={item.get('source', '')} | title={item.get('title', '')} | desc={desc}"
        # 正文素材（GitHub 用 readme，其他源用 content），压缩空白为单行避免格式错乱
        body = (item.get("readme") or item.get("content") or "").strip()[:1200]
        if body:
            line += f"\n   content={' '.join(body.split())}"
        lines.append(line)
    return USER_PROMPT_TEMPLATE.format(items="\n".join(lines))


def parse_llm_response(text: str) -> list[dict]:
    """Parse LLM response, handling markdown fences and both
    {"summaries": [...]} and bare-array shapes."""
    clean = text.strip()
    if clean.startswith("```"):
        clean = clean.split("\n", 1)[1] if "\n" in clean else clean[3:]
        clean = clean.rsplit("```", 1)[0]
    data = json.loads(clean.strip())
    if isinstance(data, dict):
        data = data.get("summaries", [])
    return data if isinstance(data, list) else []


def get_llm_provider():
    """Find first available LLM provider with API key set."""
    for provider in LLM_PROVIDERS:
        key = os.environ.get(provider["api_key_env"], "")
        # Validate key looks real (starts with sk-)
        if not key.startswith("sk-"):
            key = ""
        # Local key file fallback, scoped to its own provider
        # (否则 openai provider 会误用 deepseek 的 key)
        if not key and provider.get("api_key_file"):
            key_file = BASE_DIR / provider["api_key_file"]
            if key_file.exists():
                key = key_file.read_text().strip()
        if key:
            return {**provider, "api_key": key}
    return None


def template_summary(item: dict) -> tuple[str, str]:
    """Low-quality template fallback."""
    title = item.get("title", "")
    source = item.get("source", "")
    desc = (item.get("description") or "")[:100]
    source_labels_zh = {
        "hackernews": "HN 热门",
        "github_trending": "开源项目",
        "producthunt": "Product Hunt 热门",
        "juejin": "掘金精选",
        "zhihu": "知乎热榜",
        "36kr": "36氪热门",
        "infoq": "InfoQ 精选",
        "v2ex": "V2EX 热议",
    }
    source_labels_en = {
        "hackernews": "Trending on HN",
        "github_trending": "Open-source project",
        "producthunt": "Popular on Product Hunt",
        "juejin": "Featured on Juejin",
        "zhihu": "Hot on Zhihu",
        "36kr": "Popular on 36Kr",
        "infoq": "Featured on InfoQ",
        "v2ex": "Hot on V2EX",
    }
    label_zh = source_labels_zh.get(source, "热门")
    label_en = source_labels_en.get(source, "Trending")
    if source == "github_trending":
        name = title.split("/")[-1] if "/" in title else title
        return (f"开源项目 {name}" + (f" — {desc}" if desc else "。"),
                f"Open-source project {name}" + (f" — {desc}" if desc else "."))
    return f"{label_zh}：{title}", f"{label_en}: {title}"


def is_template_zh(zh: str) -> bool:
    return any(zh.startswith(p) for p in TEMPLATE_PREFIXES_ZH)


def item_hash(item: dict) -> str:
    """输入内容指纹（title+desc+readme/content），输入变化时触发重新摘要。"""
    raw = "|".join([
        (item.get("title") or "").strip(),
        (item.get("description") or "").strip(),
        (item.get("readme") or "").strip(),
        (item.get("content") or "").strip(),
    ])
    return hashlib.md5(raw.encode("utf-8")).hexdigest()[:12]


# 失败冷却：被 LLM 拒收/调用失败的条目 24h 内不重新入队，避免每轮重复扣费
FAIL_COOLDOWN_HOURS = 24


def _in_cooldown(entry: dict | None) -> bool:
    """条目最近失败过（failed_at 在冷却期内）→ 本轮跳过。"""
    if not entry:
        return False
    failed_at = entry.get("failed_at")
    if not failed_at:
        return False
    try:
        t = datetime.fromisoformat(str(failed_at).replace("Z", "+00:00"))
    except ValueError:
        return False
    return (datetime.now(timezone.utc) - t) < timedelta(hours=FAIL_COOLDOWN_HOURS)


def needs_summary(entry: dict | None, item: dict | None = None) -> bool:
    """summaries.json 里的一条记录是否需要（重新）生成。

    除摘要质量检查外，还比对输入指纹：
    - 指纹不一致 → 输入内容变了，重新生成
    - 历史条目无指纹：正文（readme/content）是新引入的输入，带正文的条目视为
      输入变化（首次部署后这批摘要需要基于正文重写）；其余信任现有摘要
    - 最近失败过的条目（failed_at 冷却期内）跳过，避免每轮重复扣费
    """
    if _in_cooldown(entry):
        return False
    if not entry:
        return True
    zh = (entry.get("summary_zh") or "").strip()
    if not zh or len(zh) < 50 or is_template_zh(zh):
        return True
    if not (entry.get("summary_en") or "").strip():
        return True
    if item is not None:
        cur = item_hash(item)
        if entry.get("input_hash") == cur:
            return False
        if entry.get("input_hash") or (item.get("readme") or item.get("content") or "").strip():
            return True
    return False


def backfill_hashes(summaries: dict[str, dict], items: dict[str, dict]) -> None:
    """给保留的旧摘要补写输入指纹（无 readme 的历史条目信任现有摘要）。"""
    for iid, item in items.items():
        entry = summaries.get(iid)
        if entry and not entry.get("input_hash"):
            entry["input_hash"] = item_hash(item)


def strip_internal(items: list[dict]) -> None:
    """移除 readme/content 字段（摘要的内部素材，写回 digest 前必须剥离，原地修改）。"""
    for it in items:
        it.pop("readme", None)
        it.pop("content", None)


def title_entities(title: str) -> list[str]:
    """标题里的可核验实体：≥2 字中文词、≥3 字母英文词（小写）。"""
    toks = []
    for m in re.findall(r"[\u4e00-\u9fff]{2,}", title):
        toks.append(m)
    for m in re.findall(r"[A-Za-z]{3,}", title):
        toks.append(m.lower())
    return toks


def has_title_overlap(zh: str, en: str, title: str) -> bool:
    """摘要须与标题有实体重叠，拦截 LLM 批量输出串行（内容对错条目）的错误。

    标题无实体（纯符号/太短）时跳过校验，避免误伤。
    """
    toks = title_entities(title)
    if not toks:
        return True
    blob = (zh + en).lower()
    return any(t in blob for t in toks)


def accept_entry(entry, batch_ids: set[str], titles: dict[str, str], has_body: dict[str, bool] | None = None):
    """校验一条 LLM 产物，合格返回 {"summary_zh","summary_en"}，否则 None。"""
    if not isinstance(entry, dict):
        return None
    item_id = entry.get("id")
    if item_id not in batch_ids:
        return None
    zh = (entry.get("summary_zh") or "").strip()
    en = (entry.get("summary_en") or "").strip()
    if not zh or not en:
        print(f"  [WARN] Rejected empty summary for {item_id}")
        return None
    if len(zh) < 20:
        print(f"  [WARN] Rejected too-short summary for {item_id}")
        return None
    if "|" in zh or "|" in en:
        print(f"  [WARN] Rejected bullet summary for {item_id}")
        return None
    title = titles.get(item_id, "").strip()
    if title and zh == title:
        print(f"  [WARN] Rejected title-echo summary for {item_id}")
        return None
    # 实体重叠校验只对"有正文素材"的条目启用：无正文条目的诚实声明摘要
    # （"原文是链接，未提供更多细节"）不含标题实体属正常，避免误伤
    if title and has_body and has_body.get(item_id) \
            and not has_title_overlap(zh, en, title):
        print(f"  [WARN] Rejected mismatched summary (no title overlap) for {item_id}")
        return None
    return {"summary_zh": zh, "summary_en": en}


def llm_summarize(items: list[dict], provider: dict, batch_size: int,
                  summaries: dict[str, dict], llm_ids: set[str]):
    """One pass of batched LLM summarization; results merged into `summaries`."""
    titles = {it["id"]: it.get("title", "") for it in items}
    hashes = {it["id"]: item_hash(it) for it in items}
    has_body = {it["id"]: bool(it.get("readme") or it.get("content"))
                for it in items}
    for i in range(0, len(items), batch_size):
        batch = items[i:i + batch_size]
        batch_ids = {it["id"] for it in batch}
        result = call_llm(provider["base_url"], provider["api_key"], provider["model"],
                          build_prompt(batch))
        if result:
            try:
                parsed = parse_llm_response(result)
                n = 0
                for entry in parsed:
                    ok = accept_entry(entry, batch_ids, titles, has_body)
                    if ok:
                        ok["input_hash"] = hashes[entry["id"]]
                        summaries[entry["id"]] = ok
                        llm_ids.add(entry["id"])
                        n += 1
                print(f"  Batch {i//batch_size+1}: {n}/{len(batch)} accepted")
            except json.JSONDecodeError as e:
                print(f"  [WARN] JSON parse error: {e}")
        if i + batch_size < len(items):
            time.sleep(1)


def find_items_in_history(ids: set[str]) -> dict[str, dict]:
    """从 digest + 历史快照里按 id 找回原始条目（用于空摘要回填）。"""
    found: dict[str, dict] = {}
    digest_path = FINAL_DIR / "digest.json"
    sources: list[Path] = []
    if digest_path.exists():
        sources.append(digest_path)
    if HISTORY_DIR.exists():
        sources.extend(sorted(HISTORY_DIR.glob("*.json"), reverse=True))
    for path in sources:
        if len(found) == len(ids):
            break
        try:
            data = json.loads(path.read_text())
        except (ValueError, json.JSONDecodeError):
            continue
        pools = []
        if "daily" in data:  # digest.json
            pools.append(data["daily"].get("items", []))
        else:  # history snapshot
            pools.append(data.get("digest_items", []))
            pools.append(data.get("items", []))
        for pool in pools:
            for item in pool:
                item_id = item.get("id", "")
                if item_id in ids and item_id not in found:
                    found[item_id] = item
    return found


def backfill_history_summaries(summaries: dict[str, dict], today_key: str):
    """把摘要回填进历史快照：所有快照补空字段；今日快照覆盖为最新值。"""
    if not HISTORY_DIR.exists():
        return
    for snapshot_path in sorted(HISTORY_DIR.glob("*.json")):
        overwrite = snapshot_path.stem == today_key
        try:
            data = json.loads(snapshot_path.read_text())
        except (ValueError, json.JSONDecodeError):
            continue
        updated = False
        for key in ("items", "digest_items"):
            for item in data.get(key, []):
                s = summaries.get(item.get("id", ""))
                if not s:
                    continue
                zh, en = s.get("summary_zh", ""), s.get("summary_en", "")
                if zh and (overwrite or not (item.get("summary_zh") or "").strip()):
                    item["summary_zh"] = zh
                    updated = True
                if en and (overwrite or not (item.get("summary_en") or "").strip()):
                    item["summary_en"] = en
                    updated = True
        if updated:
            try:
                snapshot_path.write_text(json.dumps(data, indent=2, ensure_ascii=False))
                print(f"[SUM] Backfilled summaries in {snapshot_path.name}")
            except Exception as e:
                print(f"[WARN] Failed to write {snapshot_path.name}: {e}", file=sys.stderr)


def main():
    digest_path = FINAL_DIR / "digest.json"
    if not digest_path.exists():
        print("[SUM] No digest.json found.")
        sys.exit(1)

    digest = json.loads(digest_path.read_text())

    existing: dict[str, dict] = {}
    if SUMMARIES_PATH.exists():
        existing = json.loads(SUMMARIES_PATH.read_text())

    # Collect unique items needing summaries
    all_items: dict[str, dict] = {}
    for key in ["daily"]:
        for item in digest[key]["items"]:
            all_items[item["id"]] = item

    need: dict[str, dict] = {
        id: item for id, item in all_items.items()
        if needs_summary(existing.get(id), item)
    }

    # 历史空摘要条目自动重新入队（不删库）：从 digest/快照找回原始条目。
    # 冷却期内（最近失败过）的空条目不重新入队，避免每轮重复扣费。
    empty_ids = {id for id, s in existing.items()
                 if not (s.get("summary_zh") or "").strip()
                 and not _in_cooldown(s)} - set(all_items)
    retry_only_ids: set[str] = set()
    if empty_ids:
        resolved = find_items_in_history(empty_ids)
        for id, item in list(resolved.items())[:MAX_RETRY_EMPTY]:
            need[id] = item
            retry_only_ids.add(id)
        unresolved = len(empty_ids) - len(resolved)
        print(f"[SUM] 历史空摘要 {len(empty_ids)} 条：重新入队 {len(retry_only_ids)}"
              + (f"，找不到原始条目跳过 {unresolved}" if unresolved else ""))
        # 清理死数据：空摘要、找不到原始条目、且无指纹/失败标记的遗留条目
        # （不可恢复，保留只会每轮被扫描）
        pruned = 0
        for id in unresolved:
            entry = existing.get(id)
            if entry and not entry.get("input_hash") and not entry.get("failed_at"):
                del existing[id]
                pruned += 1
        if pruned:
            print(f"[SUM] 清理 {pruned} 条不可恢复的空摘要死数据")

    if not need:
        print("[SUM] All items have good summaries.")
        # Still apply existing summaries to digest
        for key in ["daily"]:
            for item in digest[key]["items"]:
                s = existing.get(item["id"])
                if s:
                    item["summary_zh"] = s.get("summary_zh", "")
                    item["summary_en"] = s.get("summary_en", "")
        backfill_hashes(existing, all_items)
        SUMMARIES_PATH.write_text(json.dumps(existing, indent=2, ensure_ascii=False))
        strip_internal(digest["daily"]["items"])
        strip_internal(digest["monthly"]["items"])
        digest_path.write_text(json.dumps(digest, indent=2, ensure_ascii=False))
        return

    print(f"[SUM] {len(need)} items need summaries")

    # Try LLM first
    provider = get_llm_provider()
    summaries: dict[str, dict] = {}
    llm_ids: set[str] = set()

    if provider:
        print(f"[SUM] Using {provider['name']} API ({provider['model']})...")
        need_list = list(need.values())
        try:
            llm_summarize(need_list, provider, BATCH_SIZE, summaries, llm_ids)

            # 重试一轮：空摘要/被校验拒收/批次解析失败的条目，更小批次再试一次
            missing = [it for it in need_list if it["id"] not in summaries]
            if missing:
                print(f"[SUM] Retrying {len(missing)} failed items (smaller batches)...")
                llm_summarize(missing, provider, RETRY_BATCH_SIZE, summaries, llm_ids)
        except LLMAuthError as e:
            # key 无效：立即中止并报错，避免空转与模板垃圾污染
            print(f"[ERROR] {e} — 请检查 DEEPSEEK_API_KEY / OPENAI_API_KEY", file=sys.stderr)
            sys.exit(1)

        # 两轮后仍失败的条目：记录 failed_at/failed_count，进入 24h 冷却，
        # 下轮不再重复扣费（内容变化时 input_hash 变化会自然解除冷却——见 needs_summary）
        still_missing = [it for it in need_list if it["id"] not in summaries]
        if still_missing:
            failed_ts = datetime.now(timezone.utc).isoformat(timespec="seconds")
            for it in still_missing:
                entry = existing.get(it["id"]) or {}
                entry["failed_at"] = failed_ts
                entry["failed_count"] = int(entry.get("failed_count") or 0) + 1
                existing[it["id"]] = entry
            print(f"[SUM] 记录 {len(still_missing)} 条失败条目进入 {FAIL_COOLDOWN_HOURS}h 冷却")
    else:
        print("[SUM] No LLM API key found (set DEEPSEEK_API_KEY or OPENAI_API_KEY)")
        print("[SUM] Falling back to template summaries")

    # Fallback: template for any still missing
    # （历史回填条目不用模板兜底——留空下轮再试，避免模板垃圾污染 summaries.json）
    for id, item in need.items():
        if id not in summaries and id not in retry_only_ids:
            zh, en = template_summary(item)
            summaries[id] = {"summary_zh": zh, "summary_en": en, "input_hash": item_hash(item)}

    # Merge into existing
    existing.update(summaries)
    backfill_hashes(existing, all_items)

    # Apply to digest
    for key in ["daily"]:
        for item in digest[key]["items"]:
            s = existing.get(item["id"])
            if s:
                item["summary_zh"] = s.get("summary_zh", "")
                item["summary_en"] = s.get("summary_en", "")

    # Save（readme 仅作摘要输入，不写入最终产出）
    strip_internal(digest["daily"]["items"])
    strip_internal(digest["monthly"]["items"])
    digest_path.write_text(json.dumps(digest, indent=2, ensure_ascii=False))
    SUMMARIES_PATH.write_text(json.dumps(existing, indent=2, ensure_ascii=False))

    llm_count = len(llm_ids)
    print(f"[SUM] Done: {llm_count} LLM + {len(summaries)-llm_count} template = {len(summaries)} total")

    # 回填历史快照：今日快照覆盖为最新摘要，旧快照只补空字段
    today_key = digest.get("daily", {}).get("date", "")
    backfill_history_summaries(existing, today_key)


if __name__ == "__main__":
    main()
