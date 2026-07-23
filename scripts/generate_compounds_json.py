#!/usr/bin/env python3
"""从解析结果 CSV 生成 compounds.json（供 parse_text_ai.py 使用）。"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def cli() -> int:
    parser = argparse.ArgumentParser(description="从 CSV 生成 compounds.json")
    parser.add_argument(
        "csv",
        nargs="?",
        default=str(ROOT / "EO018 compounds list 20240809_compounds.csv"),
        help="含 Compound_ID、text 列的 CSV",
    )
    parser.add_argument(
        "-o",
        "--output",
        default=str(ROOT / "compounds.json"),
        help="输出 JSON 路径",
    )
    args = parser.parse_args()
    compounds = []
    with Path(args.csv).open(encoding="utf-8-sig", newline="") as f:
        for row in csv.DictReader(f):
            text = (row.get("text") or "").strip()
            if not text:
                continue
            compounds.append(
                {
                    "compound_id": (row.get("Compound_ID") or "").strip(),
                    "text": text,
                }
            )
    Path(args.output).write_text(
        json.dumps(compounds, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"已写入 {len(compounds)} 条到 {args.output}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(cli())
