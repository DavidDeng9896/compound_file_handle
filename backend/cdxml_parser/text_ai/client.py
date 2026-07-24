"""OpenAI 兼容 Chat Completions 客户端。"""

from __future__ import annotations

import json
from typing import Any, Dict, Optional

import httpx

from cdxml.text_ai.json_util import parse_llm_json, strip_markdown_fence, strip_think_blocks
from cdxml.text_ai.prompts import DEFAULT_SYSTEM_PROMPT, DEFAULT_USER_PROMPT_TEMPLATE


class AiClientError(Exception):
    pass


def _normalize_base_url(base_url: str) -> str:
    url = (base_url or "https://api.openai.com/v1").strip().rstrip("/")
    if not url.endswith("/v1"):
        if url.endswith("/v1/"):
            url = url.rstrip("/")
        elif "/v1" not in url:
            url = f"{url}/v1"
    return url


def _use_json_response_format(config: Dict[str, Any], base_url: str) -> bool:
    if config.get("use_json_response_format") is False:
        return False
    host = base_url.lower()
    # MiniMax 等兼容接口对 response_format 支持不稳定，默认关闭
    if "minimax" in host:
        return False
    return bool(config.get("use_json_response_format", True))


def resolve_api_key(config: Dict[str, Any]) -> str:
    import os

    key = (config.get("api_key") or "").strip()
    if key:
        return key
    return (os.environ.get("CDXML_AI_API_KEY") or "").strip()


def build_user_prompt(template: str, compound_id: str, text: str) -> str:
    tpl = template or DEFAULT_USER_PROMPT_TEMPLATE
    return tpl.format(compound_id=compound_id, text=text)


class OpenAiCompatibleClient:
    def __init__(self, config: Dict[str, Any]) -> None:
        self.config = config
        self.base_url = _normalize_base_url(config.get("base_url", ""))
        self.api_key = resolve_api_key(config)
        self.model = (config.get("model") or "gpt-4o-mini").strip()
        self.temperature = float(config.get("temperature", 0))
        self.max_tokens = int(config.get("max_tokens", 4096))
        self.system_prompt = (config.get("system_prompt") or DEFAULT_SYSTEM_PROMPT).strip()
        self.user_prompt_template = config.get("user_prompt_template") or DEFAULT_USER_PROMPT_TEMPLATE
        self.timeout = float(config.get("timeout", 120))
        self.use_json_response_format = _use_json_response_format(config, self.base_url)

    def ensure_configured(self) -> None:
        if not self.api_key:
            raise AiClientError("未配置 API Key（请在设置中填写或设置环境变量 CDXML_AI_API_KEY）")

    def chat_json(
        self,
        user_content: str,
        *,
        system_prompt: Optional[str] = None,
    ) -> Dict[str, Any]:
        self.ensure_configured()
        url = f"{self.base_url}/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        body: Dict[str, Any] = {
            "model": self.model,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "messages": [
                {"role": "system", "content": system_prompt or self.system_prompt},
                {"role": "user", "content": user_content},
            ],
        }
        if self.use_json_response_format:
            body["response_format"] = {"type": "json_object"}

        try:
            with httpx.Client(timeout=self.timeout) as client:
                resp = client.post(url, headers=headers, json=body)
        except httpx.HTTPError as e:
            raise AiClientError(f"网络请求失败: {e}") from e

        if resp.status_code >= 400:
            detail = resp.text[:500]
            raise AiClientError(f"API 错误 HTTP {resp.status_code}: {detail}")

        try:
            payload = resp.json()
            content = payload["choices"][0]["message"]["content"]
        except (KeyError, IndexError, json.JSONDecodeError) as e:
            raise AiClientError(f"API 响应格式异常: {e}") from e

        if content is None:
            raise AiClientError("模型返回空内容")

        raw = strip_markdown_fence(strip_think_blocks(str(content)))
        try:
            return parse_llm_json(raw)
        except json.JSONDecodeError as e:
            snippet = raw[:300].replace("\n", "\\n")
            raise AiClientError(
                f"模型返回非合法 JSON: {e}; 片段: {snippet}"
            ) from e

    def parse_compound_text(self, compound_id: str, text: str) -> Dict[str, Any]:
        user = build_user_prompt(self.user_prompt_template, compound_id, text)
        try:
            data = self.chat_json(user)
        except AiClientError as first_err:
            if "非合法 JSON" not in str(first_err):
                raise
            repair = (
                "上一次输出不是合法 JSON。请仅输出一个可被 json.loads 解析的 JSON 对象：\n"
                "- 所有键名与字符串值必须使用英文双引号\n"
                "- 不要使用注释、尾逗号、单引号\n"
                "- 缺失字段用 null，数组无数据用 []\n\n"
                f"Compound_ID: {compound_id}\n\ntext:\n{text}"
            )
            data = self.chat_json(
                repair,
                system_prompt=(self.system_prompt + "\n\n仅输出严格 JSON，不要 markdown。"),
            )
        if not data.get("compound_id"):
            data["compound_id"] = compound_id
        return data

    def test_connection(self) -> Dict[str, Any]:
        from cdxml.text_ai.prompts import TEST_USER_PROMPT

        data = self.chat_json(
            TEST_USER_PROMPT,
            system_prompt='只回复 JSON 对象 {"ok": true}，不要其他文字。',
        )
        if data.get("ok") is True:
            return {"success": True, "message": "连接成功"}
        return {"success": True, "message": f"连接成功（模型返回: {data})"}
