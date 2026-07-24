"""6 表字段定义、JSON Schema 与展平逻辑。"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

import jsonschema

# CSV 表头（与用户 schema 一致）
IC50_HEADERS = [
    "Compound_ID",
    "Cell_line",
    "IC50(nM)",
    "IC50_SD",
    "Top（%）",
    "Positive control",
    "构型",
]

AUC_HEADERS = [
    "Compound_ID",
    "Species",
    "AUC₀₋t（h·ng/mL）",
    "F%",
    "给药剂量(mpk)",
]

FU_HEADERS = [
    "Compound_ID",
    "Species",
    "Fu(%)",
]

SOLUBILITY_HEADERS = [
    "Compound_ID",
    "溶出介质",
    "Solubility(μg/mL)",
    "pH",
]

MMS_HEADERS = [
    "Compound_ID",
    "Species",
    "MMS T1/2 (min)",
    "检测方法",
]

CYP_HEADERS = [
    "Compound_ID",
    "CYP酶亚型",
    "检测浓度（μM）",
    "抑制率 inhibition（%）",
]

TABLE_NAMES = ("ic50", "auc", "fu", "solubility", "mms", "cyp_inhibition")

TABLE_HEADERS: Dict[str, List[str]] = {
    "ic50": IC50_HEADERS,
    "auc": AUC_HEADERS,
    "fu": FU_HEADERS,
    "solubility": SOLUBILITY_HEADERS,
    "mms": MMS_HEADERS,
    "cyp_inhibition": CYP_HEADERS,
}

CSV_FILENAMES = {
    "ic50": "IC50.csv",
    "auc": "AUC0_t.csv",
    "fu": "Fu.csv",
    "solubility": "Solubility.csv",
    "mms": "MMS_T12.csv",
    "cyp_inhibition": "CYP_inhibition.csv",
}

COMPOUND_RESPONSE_SCHEMA: Dict[str, Any] = {
    "type": "object",
    "required": ["compound_id"],
    "properties": {
        "compound_id": {"type": "string"},
        "ic50": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "cell_line": {"type": ["string", "null"]},
                    "ic50_nm": {"type": ["number", "string", "null"]},
                    "ic50_sd": {"type": ["number", "null"]},
                    "top_percent": {"type": ["number", "null"]},
                    "positive_control": {"type": ["string", "number", "null"]},
                    "stereochemistry": {"type": ["string", "null"]},
                },
            },
        },
        "auc": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "species": {"type": ["string", "null"]},
                    "auc_h_ng_ml": {"type": ["number", "null"]},
                    "f_percent": {"type": ["number", "null"]},
                    "dose_mpk": {"type": ["number", "null"]},
                },
            },
        },
        "fu": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "species": {"type": ["string", "null"]},
                    "fu_percent": {"type": ["number", "null"]},
                },
            },
        },
        "solubility": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "medium": {"type": ["string", "null"]},
                    "solubility_ug_ml": {"type": ["number", "string", "null"]},
                    "ph": {"type": ["number", "null"]},
                },
            },
        },
        "mms": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "species": {"type": ["string", "null"]},
                    "t12_min": {"type": ["number", "null"]},
                    "method": {"type": ["string", "null"]},
                },
            },
        },
        "cyp_inhibition": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "isoform": {"type": ["string", "null"]},
                    "concentration_um": {"type": ["number", "null"]},
                    "inhibition_percent": {"type": ["number", "null"]},
                },
            },
        },
        "unparsed_lines": {"type": "array", "items": {"type": "string"}},
        "warnings": {"type": "array", "items": {"type": "string"}},
    },
    "additionalProperties": True,
}


def _cell(value: Any) -> str:
    if value is None:
        return ""
    return str(value)


def validate_compound_response(data: Dict[str, Any]) -> None:
    jsonschema.validate(instance=data, schema=COMPOUND_RESPONSE_SCHEMA)


def flatten_to_tables(
    compounds: List[Dict[str, Any]],
) -> Dict[str, List[Dict[str, str]]]:
    """将多条化合物 AI 解析结果展平为 6 张表行列表。"""
    tables: Dict[str, List[Dict[str, str]]] = {name: [] for name in TABLE_NAMES}

    for item in compounds:
        cid = item.get("compound_id") or ""
        parsed = item.get("parsed") or {}
        if item.get("error"):
            continue
        if not parsed:
            continue

        for row in parsed.get("ic50") or []:
            tables["ic50"].append(
                {
                    "Compound_ID": cid,
                    "Cell_line": _cell(row.get("cell_line")),
                    "IC50(nM)": _cell(row.get("ic50_nm")),
                    "IC50_SD": _cell(row.get("ic50_sd")),
                    "Top（%）": _cell(row.get("top_percent")),
                    "Positive control": _cell(row.get("positive_control")),
                    "构型": _cell(row.get("stereochemistry")),
                }
            )

        for row in parsed.get("auc") or []:
            tables["auc"].append(
                {
                    "Compound_ID": cid,
                    "Species": _cell(row.get("species")),
                    "AUC₀₋t（h·ng/mL）": _cell(row.get("auc_h_ng_ml")),
                    "F%": _cell(row.get("f_percent")),
                    "给药剂量(mpk)": _cell(row.get("dose_mpk")),
                }
            )

        for row in parsed.get("fu") or []:
            tables["fu"].append(
                {
                    "Compound_ID": cid,
                    "Species": _cell(row.get("species")),
                    "Fu(%)": _cell(row.get("fu_percent")),
                }
            )

        for row in parsed.get("solubility") or []:
            tables["solubility"].append(
                {
                    "Compound_ID": cid,
                    "溶出介质": _cell(row.get("medium")),
                    "Solubility(μg/mL)": _cell(row.get("solubility_ug_ml")),
                    "pH": _cell(row.get("ph")),
                }
            )

        for row in parsed.get("mms") or []:
            tables["mms"].append(
                {
                    "Compound_ID": cid,
                    "Species": _cell(row.get("species")),
                    "MMS T1/2 (min)": _cell(row.get("t12_min")),
                    "检测方法": _cell(row.get("method")),
                }
            )

        for row in parsed.get("cyp_inhibition") or []:
            tables["cyp_inhibition"].append(
                {
                    "Compound_ID": cid,
                    "CYP酶亚型": _cell(row.get("isoform")),
                    "检测浓度（μM）": _cell(row.get("concentration_um")),
                    "抑制率 inhibition（%）": _cell(row.get("inhibition_percent")),
                }
            )

    return tables


def empty_tables() -> Dict[str, List[Dict[str, str]]]:
    return {name: [] for name in TABLE_NAMES}
