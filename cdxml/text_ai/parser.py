"""单条化合物 text 的 AI 解析与校验。"""

from __future__ import annotations

import json
from typing import Any, Dict, Optional

from cdxml.text_ai.client import AiClientError, OpenAiCompatibleClient
from cdxml.text_ai.schema import validate_compound_response


def parse_compound_with_ai(
    client: OpenAiCompatibleClient,
    compound_id: str,
    text: str,
    *,
    max_retries: int = 2,
) -> Dict[str, Any]:
    """调用 AI 解析单条 text，校验 JSON schema。"""
    last_err: Optional[Exception] = None
    for attempt in range(max_retries + 1):
        try:
            data = client.parse_compound_text(compound_id, text)
            validate_compound_response(data)
            return data
        except (AiClientError, json.JSONDecodeError, Exception) as e:
            last_err = e
            if attempt >= max_retries:
                break
    raise AiClientError(str(last_err) if last_err else "解析失败")
