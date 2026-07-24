"""json_util 单元测试。"""

import json

import pytest

from cdxml.text_ai.json_util import parse_llm_json


def test_parse_trailing_comma() -> None:
    raw = '{"a": 1, "b": [2,],}'
    obj = parse_llm_json(raw)
    assert obj["a"] == 1


def test_parse_markdown_fence() -> None:
    raw = '```json\n{"ok": true}\n```'
    assert parse_llm_json(raw)["ok"] is True


def test_parse_unquoted_like_repair() -> None:
    raw = "{'compound_id': 'HW1', 'ic50': []}"
  # json_repair should handle single quotes
    obj = parse_llm_json(raw)
    assert obj["compound_id"] == "HW1"


def test_parse_invalid_raises() -> None:
    with pytest.raises(json.JSONDecodeError):
        parse_llm_json("not json at all")


def test_parse_minimax_think_block() -> None:
    """MiniMax 等模型会在 content 里夹带 <think> 推理，需剥离后再解析。"""
    raw = (
        "<think>\n"
        'The user wants {"ok": true} only. Mention {"ok": false} as wrong.\n'
        "</think>\n\n"
        '{"ok": true}'
    )
    assert parse_llm_json(raw)["ok"] is True
