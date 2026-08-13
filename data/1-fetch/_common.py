"""Fetch 脚本共享工具：HTML 正文提取（纯标准库）。

用法：
    from _common import html_to_text
    text = html_to_text(page_html, max_chars=2000)
    text = html_to_text(page_html, max_chars=2000, target_class="ProseMirror")
"""

from __future__ import annotations

from html.parser import HTMLParser


class TextExtractor(HTMLParser):
    """提取 HTML 纯文本：忽略 script/style，可选限定在某个 class 的 div 容器内。"""

    def __init__(self, target_class: str | None = None):
        super().__init__()
        self.target_class = target_class
        self.parts: list[str] = []
        self._skip = 0        # script/style 嵌套深度
        # target_class 为空时收集整页文本
        self._capture = target_class is None
        self._depth = 0       # 目标容器 div 嵌套深度（仅 target_class 模式使用）

    def handle_starttag(self, tag, attrs):
        if tag in ("script", "style"):
            self._skip += 1
        if self._capture and self.target_class:
            if tag == "div":
                self._depth += 1
        elif self.target_class:
            cls = dict(attrs).get("class", "") or ""
            if self.target_class in cls.split():
                self._capture = True
                self._depth = 1

    def handle_endtag(self, tag):
        if tag in ("script", "style"):
            if self._skip:
                self._skip -= 1
            return
        # 全页模式不追踪 div 深度：此前在第一个顶层 </div> 就停止捕获，
        # 导致后续平级内容（如第二个正文 div）全部丢失（实测）
        if self._capture and self.target_class and tag == "div":
            self._depth -= 1
            if self._depth <= 0:
                self._capture = False

    def handle_data(self, data):
        if self._capture and not self._skip:
            self.parts.append(data)


def html_to_text(html: str, max_chars: int = 2000, target_class: str | None = None) -> str:
    """HTML → 压缩空白的纯文本，截断到 max_chars。解析失败返回空串。"""
    try:
        ex = TextExtractor(target_class)
        ex.feed(html)
        text = " ".join(" ".join(ex.parts).split())
        return text[:max_chars]
    except Exception:
        return ""
