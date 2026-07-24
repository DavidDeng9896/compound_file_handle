"""CDXML 化合物解析：结构提取、空间匹配与 CSV 导出。"""

from cdxml_parser.parser import (
    ParseResult,
    has_x_overlap,
    main,
    parse_fragment_to_smiles,
    parse_result_to_json_dict,
    resolve_bbox_fragment,
    resolve_bbox_t,
)

__all__ = [
    "ParseResult",
    "has_x_overlap",
    "main",
    "parse_fragment_to_smiles",
    "parse_result_to_json_dict",
    "resolve_bbox_fragment",
    "resolve_bbox_t",
]
