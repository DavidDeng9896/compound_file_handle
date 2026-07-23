#!/usr/bin/env python3
"""导出 CDXML 解析审查清单（未匹配 HW、结构等）。"""

from __future__ import annotations

import argparse
import sys

from cdxml.parser import main
from cdxml.review import export_review_csv


def cli() -> int:
    parser = argparse.ArgumentParser(description="解析 CDXML 并导出审查清单 CSV")
    parser.add_argument("cdxml", help="输入 .cdxml 文件路径")
    parser.add_argument(
        "-o",
        "--output",
        default="review_unmatched.csv",
        help="输出审查清单 CSV（默认 review_unmatched.csv）",
    )
    parser.add_argument("--match-x-left", type=float, default=0.0, help="结构框 X 左扩展")
    parser.add_argument("--match-x-right", type=float, default=0.0, help="结构框 X 右扩展")
    parser.add_argument("--match-y-down", type=float, default=130.0, help="Y/距离匹配上限")
    args = parser.parse_args()

    result = main(
        args.cdxml,
        None,
        match_x_extend_left=args.match_x_left,
        match_x_extend_right=args.match_x_right,
        match_y_down=args.match_y_down,
    )
    if not result.success:
        print(result.message or "解析失败", file=sys.stderr)
        return 1

    export_review_csv(args.output, result)
    print(f"审查清单已写入: {args.output}")
    print(f"  未匹配 HW: {len(result.unmatched_hw)}")
    print(f"  未匹配结构: {len(result.unmatched_structures)}")
    print(f"  未用属性行: {len(result.unused_property_texts)}")
    print(f"  未匹配其他文字: {len(result.unused_other_texts)}")
    print(f"  SMILES 为空: {len(result.matched_but_empty_smiles)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(cli())
