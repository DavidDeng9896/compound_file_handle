"""AI 配置：空提示词回退到代码默认模板。"""

from __future__ import annotations

import json
from pathlib import Path

from cdxml_parser.text_ai.prompts import DEFAULT_SYSTEM_PROMPT, DEFAULT_USER_PROMPT_TEMPLATE


def test_load_ai_config_blank_prompt_falls_back(tmp_path, monkeypatch):
    import app.main as main

    cfg_path = tmp_path / "ai_config.json"
    cfg_path.write_text(
        json.dumps(
            {
                "base_url": "https://example.com/v1",
                "model": "demo",
                "system_prompt": "",
                "user_prompt_template": "   ",
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(main, "CONFIG_PATH", cfg_path)
    cfg = main._load_ai_config()
    assert cfg["system_prompt"] == DEFAULT_SYSTEM_PROMPT
    assert cfg["user_prompt_template"] == DEFAULT_USER_PROMPT_TEMPLATE
    assert cfg["model"] == "demo"


def test_public_ai_config_includes_defaults():
    import app.main as main

    pub = main._public_ai_config(main._load_ai_config())
    assert pub["default_system_prompt"] == DEFAULT_SYSTEM_PROMPT
    assert pub["default_user_prompt_template"] == DEFAULT_USER_PROMPT_TEMPLATE
    assert (pub.get("system_prompt") or "").strip()


def test_save_does_not_persist_blank_prompts(tmp_path, monkeypatch):
    import app.main as main

    cfg_path = tmp_path / "ai_config.json"
    monkeypatch.setattr(main, "CONFIG_PATH", cfg_path)
    saved = main._save_ai_config(
        {
            "model": "x",
            "system_prompt": "",
            "user_prompt_template": "",
        }
    )
    assert saved["system_prompt"] == DEFAULT_SYSTEM_PROMPT
    disk = json.loads(cfg_path.read_text(encoding="utf-8"))
    assert disk["system_prompt"] == DEFAULT_SYSTEM_PROMPT


def test_save_persists_user_settings_and_ignores_parse_cache_flag(tmp_path, monkeypatch):
    import app.main as main

    cfg_path = tmp_path / "ai_config.json"
    monkeypatch.setattr(main, "CONFIG_PATH", cfg_path)
    first = main._save_ai_config(
        {
            "base_url": "https://api.minimaxi.com/v1",
            "api_key": "sk-test",
            "model": "MiniMax-M2.7-highspeed",
            "system_prompt": "custom prompt",
            "use_cache": True,
        }
    )
    assert first["base_url"] == "https://api.minimaxi.com/v1"
    assert first["model"] == "MiniMax-M2.7-highspeed"
    assert first["system_prompt"] == "custom prompt"
    assert first["use_cache"] is False

    second = main._save_ai_config({"model": "MiniMax-M2.7-highspeed"})
    assert second["api_key"] == "sk-test"
    assert second["system_prompt"] == "custom prompt"
    assert second["use_cache"] is False


def test_load_forces_parse_cache_off(tmp_path, monkeypatch):
    import app.main as main

    cfg_path = tmp_path / "ai_config.json"
    cfg_path.write_text(
        json.dumps({"model": "keep-me", "use_cache": True, "system_prompt": "keep"}, ensure_ascii=False),
        encoding="utf-8",
    )
    monkeypatch.setattr(main, "CONFIG_PATH", cfg_path)
    cfg = main._load_ai_config()
    assert cfg["model"] == "keep-me"
    assert cfg["system_prompt"] == "keep"
    assert cfg["use_cache"] is False
