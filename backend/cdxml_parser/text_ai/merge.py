"""将 6 张结构化表按 Compound_ID 横向连表合并。"""

from __future__ import annotations

from collections import OrderedDict
from typing import Any, Dict, List, Sequence, Tuple

from cdxml.text_ai.schema import TABLE_HEADERS, TABLE_NAMES

# 合并表中子列不重复带 Compound_ID
_SKIP_KEYS = frozenset({"Compound_ID"})


def _group_rows_by_id(
    rows: Sequence[Dict[str, Any]],
) -> "OrderedDict[str, List[Dict[str, Any]]]":
    grouped: "OrderedDict[str, List[Dict[str, Any]]]" = OrderedDict()
    for row in rows or []:
        cid = str(row.get("Compound_ID") or "").strip()
        if not cid:
            continue
        grouped.setdefault(cid, []).append(row)
    return grouped


def merge_column_defs() -> List[Dict[str, Any]]:
    """供前端/导出使用的两级表头定义。"""
    groups: List[Dict[str, Any]] = [
        {"label": "Compound_ID", "prop": "Compound_ID", "children": None}
    ]
    for name in TABLE_NAMES:
        children = []
        for h in TABLE_HEADERS[name]:
            if h in _SKIP_KEYS:
                continue
            children.append({"label": h, "prop": f"{name}__{h}"})
        groups.append({"label": name, "prop": name, "children": children})
    return groups


def merge_tables_by_compound_id(
    tables: Dict[str, List[Dict[str, Any]]] | None,
    *,
    compound_id_order: Sequence[str] | None = None,
) -> Tuple[List[Dict[str, str]], List[Dict[str, Any]]]:
    """
    以 Compound_ID 为主键横向合并各表。

    - 同一 Compound_ID 的第 N 条记录横向对齐
    - 行数 = 该 ID 在各表中的最大条数
    - 保留全部原始记录，不丢弃重复

    Returns:
        (merged_rows, column_defs)
    """
    tables = tables or {}
    grouped: Dict[str, Dict[str, List[Dict[str, Any]]]] = {
        name: _group_rows_by_id(tables.get(name) or []) for name in TABLE_NAMES
    }

    if compound_id_order:
        order: List[str] = []
        seen = set()
        for cid in compound_id_order:
            c = str(cid or "").strip()
            if c and c not in seen:
                order.append(c)
                seen.add(c)
        for name in TABLE_NAMES:
            for cid in grouped[name].keys():
                if cid not in seen:
                    order.append(cid)
                    seen.add(cid)
    else:
        order = []
        seen = set()
        for name in TABLE_NAMES:
            for cid in grouped[name].keys():
                if cid not in seen:
                    order.append(cid)
                    seen.add(cid)

    merged: List[Dict[str, str]] = []
    for cid in order:
        per_table = {name: grouped[name].get(cid, []) for name in TABLE_NAMES}
        n = max((len(rows) for rows in per_table.values()), default=0)
        if n == 0:
            continue
        for i in range(n):
            row: Dict[str, str] = {"Compound_ID": cid}
            for name in TABLE_NAMES:
                src = per_table[name][i] if i < len(per_table[name]) else None
                for h in TABLE_HEADERS[name]:
                    if h in _SKIP_KEYS:
                        continue
                    key = f"{name}__{h}"
                    row[key] = "" if src is None else str(src.get(h, "") or "")
            merged.append(row)

    return merged, merge_column_defs()
