"""3-process 共享工具：统一时间/域名解析与中文碎词过滤规则。

各脚本独立运行（sys.path[0] 即本目录），直接 `from _shared import ...` 即可；
scripts/ 下的脚本通过 sys.path 引导导入。
"""

from __future__ import annotations

import re
from datetime import datetime, timezone
from urllib.parse import urlparse


def parse_time(t) -> datetime | None:
    """统一时间解析：ISO 字符串或 int/float 时间戳（秒/毫秒/微秒）。

    毫秒/微秒通过循环缩放到秒（36kr/infoq 用毫秒；1e15 量级微秒
    一次除法后仍 >1e12 会被误当秒解释为 1970 年附近，循环缩放修复）。
    解析失败返回 None。
    """
    try:
        if isinstance(t, (int, float)) and not isinstance(t, bool) and t > 0:
            while t >= 1e12:
                t = t / 1000
            return datetime.fromtimestamp(t, tz=timezone.utc)
        s = str(t)
        if s.isdigit():
            n = int(s)
            while n >= 1e12:
                n = n / 1000
            return datetime.fromtimestamp(n, tz=timezone.utc)
        dt = datetime.fromisoformat(s.replace("Z", "+00:00"))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt
    except (ValueError, TypeError, OSError, OverflowError):
        return None


def extract_domain(url: str) -> str:
    """域名归一化：小写 + 仅剥离前缀 www.（统一口径，勿用 replace 删所有 www.）。"""
    try:
        host = urlparse(url).hostname or ""
        return host.lower().removeprefix("www.")
    except (ValueError, TypeError):
        return ""


# --- 中文滑窗碎词过滤规则（enrich/build_trends 共用，勿分叉） ---

# 中文虚字：几乎不可能出现在合法技术话题词中，用于过滤滑窗碎片
CN_FUNC_CHARS = set(
    "的了和是我你他她它们在就不都也还与及或被把让呢吗吧啊嘛么"
    "之其于以而且若因又再才只却并将能可要想说等该此哪谁什怎没有着过得地"
)

# 含这些子串的滑窗词直接丢弃（疑问句式碎片）
CN_JUNK_SUBSTR = ("如何", "为什么")

# 整词无意义的中文短语
CN_STOP_PHRASES = {
    "这个", "那个", "什么", "怎么", "可以", "不是", "没有", "已经", "因为",
    "所以", "但是", "如果", "虽然", "知道", "觉得", "可能", "应该", "现在",
    "今天", "明天", "昨天", "大家", "自己", "问题", "东西", "事情", "怎么样",
    "为什么", "这么", "那么", "还是", "就是", "这些", "那些", "一种", "一个",
    # 标题高频元词，不是话题
    "看待", "带来", "个月", "推出", "上线", "发布", "宣布", "据悉",
    "开始", "近日", "最近", "最新", "公司", "行业", "全面", "分享", "半年",
    "时代", "多少",
    # 社区版块名泄漏（V2EX 标题前缀 "[问与答] xxx" 等）
    "分享创造", "分享发现", "分享邀请码", "分享优惠", "问与答", "酷工作",
    "奇思妙想", "职场话题", "二手交易", "免费赠送",
}


def cjk_tag_ok(gram: str) -> bool:
    """中文标签合法性：非停用短语、无疑问前缀、不含虚字。"""
    if gram in CN_STOP_PHRASES:
        return False
    if any(j in gram for j in CN_JUNK_SUBSTR):
        return False
    return not any(c in CN_FUNC_CHARS for c in gram)
