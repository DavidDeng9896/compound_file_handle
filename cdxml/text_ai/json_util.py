"""从 LLM 文本中提取并修复 JSON。"""

from __future__ import annotations

import json
import re
from typing import Any, Dict


def strip_markdown_fence(text: str) -> str:
    s = text.strip()
    m = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", s, re.IGNORECASE)
    if m:
        return m.group(1).strip()
    return s


def strip_think_blocks(text: str) -> str:
    """剥离模型推理标签（MiniMax/部分 thinking 模型会夹在 content 里）。"""
    s = text or ""
    # 闭合标签；若缺失结束标签则剥到文末
    for tag in ("think", "thinking", "reasoning"):
        s = re.sub(
            rf"<{tag}\b[^>]*>[\s\S]*?(?:</{tag}>|$)",
            "",
            s,
            flags=re.IGNORECASE,
        )
    return s.strip()


def extract_brace_block(text: str) -> str:
    s = strip_markdown_fence(strip_think_blocks(text))
    start = s.find("{")
    end = s.rfind("}")
    if start >= 0 and end > start:
        return s[start : end + 1]
    return s


def _remove_trailing_commas(s: str) -> str:
    return re.sub(r",(\s*[}\]])", r"\1", s)


def _remove_line_comments(s: str) -> str:
    return re.sub(r"//[^\n]*", "", s)


def parse_llm_json(text: str) -> Dict[str, Any]:
    """多策略解析模型输出的 JSON。"""
    if not text or not str(text).strip():
        raise json.JSONDecodeError("empty content", text or "", 0)

    candidates: list[str] = []
    raw = strip_think_blocks(text.strip())
    blob = extract_brace_block(raw)
    for item in (raw, blob, _remove_trailing_commas(blob), _remove_line_comments(blob)):
        item = item.strip()
        if item and item not in candidates:
            candidates.append(item)

    last_err: json.JSONDecodeError | None = None
    for candidate in candidates:
        try:
            obj = json.loads(candidate)
            if isinstance(obj, dict):
                return obj
        except json.JSONDecodeError as e:
            last_err = e

    try:
        from json_repair import repair_json

        repaired = repair_json(blob or raw)
        obj = json.loads(repaired)
        if isinstance(obj, dict):
            return obj
    except Exception as e:
        if last_err is None:
            raise json.JSONDecodeError(str(e), text, 0) from e

    if last_err is not None:
        raise last_err
    raise json.JSONDecodeError("无法解析 JSON", text, 0)
