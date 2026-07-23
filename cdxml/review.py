"""审查清单 CSV 导出（GUI 与命令行脚本共用）。"""

from __future__ import annotations

import csv

from cdxml.parser import ParseResult


def export_review_csv(path: str, result: ParseResult) -> None:
    """将未匹配/待复核项导出为 UTF-8-BOM CSV，便于在 Excel 中打开。"""
    with open(path, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f)
        w.writerow(["类型", "说明/内容", "X1", "Y1", "X2", "Y2", "中心X", "中心Y", "SMILES"])

        w.writerow([])
        w.writerow(["=== 未匹配的 HW 文字（未能关联到结构）==="])
        for r in result.unmatched_hw:
            w.writerow(
                [
                    "HW",
                    r.get("content", ""),
                    f"{r['x1']:.2f}",
                    f"{r['y1']:.2f}",
                    f"{r['x2']:.2f}",
                    f"{r['y2']:.2f}",
                    f"{r['center_x']:.2f}",
                    f"{r['center_y']:.2f}",
                    "",
                ]
            )

        w.writerow([])
        w.writerow(["=== 未匹配的结构（无对应 HW）==="])
        for r in result.unmatched_structures:
            w.writerow(
                [
                    "结构",
                    str(r.get("structure_index", "")),
                    f"{r['x1']:.2f}",
                    f"{r['y1']:.2f}",
                    f"{r['x2']:.2f}",
                    f"{r['y2']:.2f}",
                    f"{r['center_x']:.2f}",
                    f"{r['center_y']:.2f}",
                    r.get("smiles", "") or "",
                ]
            )

        w.writerow([])
        w.writerow(["=== 未关联到化合物的 tPSA/CLogP 文本行 ==="])
        for r in result.unused_property_texts:
            w.writerow(
                [
                    "属性行",
                    r.get("content", ""),
                    f"{r['x1']:.2f}",
                    f"{r['y1']:.2f}",
                    f"{r['x2']:.2f}",
                    f"{r['y2']:.2f}",
                    f"{r['center_x']:.2f}",
                    f"{r['center_y']:.2f}",
                    "",
                ]
            )

        w.writerow([])
        w.writerow(["=== 未匹配到其他属性文字 ==="])
        for r in result.unused_other_texts:
            w.writerow(
                [
                    "其他文字",
                    r.get("content", ""),
                    f"{r['x1']:.2f}",
                    f"{r['y1']:.2f}",
                    f"{r['x2']:.2f}",
                    f"{r['y2']:.2f}",
                    f"{r['center_x']:.2f}",
                    f"{r['center_y']:.2f}",
                    "",
                ]
            )

        w.writerow([])
        w.writerow(["=== 已匹配 HW 但 SMILES 为空（RDKit 未生成或失败）==="])
        for r in result.matched_but_empty_smiles:
            w.writerow(
                [
                    "空SMILES",
                    r.get("Compound_ID", ""),
                    f"{r['x1']:.2f}",
                    f"{r['y1']:.2f}",
                    f"{r['x2']:.2f}",
                    f"{r['y2']:.2f}",
                    f"{r['center_x']:.2f}",
                    f"{r['center_y']:.2f}",
                    "",
                ]
            )
