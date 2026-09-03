"""文本解析不走结果缓存。"""

from __future__ import annotations

from cdxml_parser.text_ai import batch as batch_mod
from cdxml_parser.text_ai.batch import _text_hash, run_batch


def test_run_batch_ignores_existing_parse_cache(tmp_path, monkeypatch):
    text = "Mouse po AUC = 10 h*ng/mL (20), F% = 5"
    cache_file = tmp_path / "text_ai_cache.json"
    cache_file.write_text(
        __import__("json").dumps(
            {
                _text_hash(text): {
                    "compound_id": "OLD",
                    "auc": [
                        {
                            "species": "mouse",
                            "route": None,
                            "auc_h_ng_ml": 999,
                            "f_percent": None,
                            "dose_mpk": None,
                        }
                    ],
                    "ic50": [],
                    "fu": [],
                    "solubility": [],
                    "mms": [],
                    "cyp_inhibition": [],
                    "unparsed_lines": [],
                    "warnings": [],
                }
            }
        ),
        encoding="utf-8",
    )

    calls = {"n": 0}

    def fake_parse(client, cid, src):
        calls["n"] += 1
        return {
            "compound_id": cid,
            "auc": [
                {
                    "species": "mouse",
                    "route": "PO",
                    "auc_h_ng_ml": 10,
                    "f_percent": 5,
                    "dose_mpk": None,
                }
            ],
            "ic50": [],
            "fu": [],
            "solubility": [],
            "mms": [],
            "cyp_inhibition": [],
            "unparsed_lines": [],
            "warnings": [],
        }

    monkeypatch.setattr(batch_mod, "parse_compound_with_ai", fake_parse)
    monkeypatch.setattr(
        batch_mod.OpenAiCompatibleClient,
        "ensure_configured",
        lambda self: None,
    )

    logs: list[str] = []
    result = run_batch(
        {
            "base_url": "https://example.com/v1",
            "api_key": "x",
            "model": "demo",
            "use_cache": True,
            "cache_dir": str(tmp_path),
        },
        [{"compound_id": "HW1", "text": text}],
        log=lambda *a: logs.append(" ".join(str(x) for x in a)),
    )
    assert calls["n"] == 1
    assert not any("[缓存]" in line for line in logs)
    auc = result["tables"]["auc"][0]
    assert auc["给药途径"] == "PO"
    assert auc["AUC₀₋t（h·ng/mL）"] == "10"
