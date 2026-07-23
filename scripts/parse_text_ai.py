#!/usr/bin/env python3
"""CLI：对 compounds JSON 批量 AI 结构化 text 并导出 6 表 CSV。"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from cdxml.text_ai.batch import default_cache_dir, run_batch
from cdxml.text_ai.client import resolve_api_key
from cdxml.text_ai.export_csv import export_tables_to_dir


def cli() -> int:
    parser = argparse.ArgumentParser(description="AI 结构化化合物 text 字段")
    parser.add_argument("--config", required=True, help="ai_config.json 路径")
    parser.add_argument("--input", required=True, help="compounds JSON（含 compound_id、text 数组）")
    parser.add_argument("-o", "--output", required=True, help="输出目录（6 个 CSV）")
    args = parser.parse_args()

    config = json.loads(Path(args.config).read_text(encoding="utf-8"))
    if not config.get("cache_dir"):
        config["cache_dir"] = default_cache_dir()

    if not resolve_api_key(config):
        print(
            "未配置 API Key：请在 ai_config.json 填写 api_key，或设置环境变量 CDXML_AI_API_KEY",
            file=sys.stderr,
        )
        return 1

    body = json.loads(Path(args.input).read_text(encoding="utf-8"))
    compounds = body if isinstance(body, list) else body.get("compounds") or []

    def log(*a: object) -> None:
        print(*a, file=sys.stderr)

    payload = run_batch(config, compounds, log=log)
    if not payload.get("tables"):
        print(payload.get("message") or "无结果", file=sys.stderr)
        return 1

    written = export_tables_to_dir(payload["tables"], args.output)
    print(f"已写入 {len(written)} 个文件到 {args.output}", file=sys.stderr)
    print(payload.get("message") or "", file=sys.stderr)
    return 0 if payload.get("success_count", 0) > 0 else 1


if __name__ == "__main__":
    raise SystemExit(cli())
