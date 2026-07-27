"""命令行：python -m cdxml_parser <cdxml> [-o output.csv]"""

from __future__ import annotations

import argparse

from cdxml_parser.parser import main


def cli() -> None:
    parser = argparse.ArgumentParser(description="从 CDXML 提取化合物并生成 CSV")
    parser.add_argument("cdxml", help="输入 .cdxml 文件路径")
    parser.add_argument(
        "-o",
        "--output",
        default="compounds_output.csv",
        help="输出 CSV 路径（默认 compounds_output.csv）",
    )
    parser.add_argument("--match-x-left", type=float, default=0.0, help="结构框 X 左扩展")
    parser.add_argument("--match-x-right", type=float, default=0.0, help="结构框 X 右扩展")
    parser.add_argument("--match-y-down", type=float, default=130.0, help="Y/距离匹配上限")
    args = parser.parse_args()
    result = main(
        args.cdxml,
        args.output,
        match_x_extend_left=args.match_x_left,
        match_x_extend_right=args.match_x_right,
        match_y_down=args.match_y_down,
    )
    if not result.success:
        raise SystemExit(result.message or "解析失败")


if __name__ == "__main__":
    cli()
