"""HW180002 / HW180003 / HW181079 回归：schema 校验与展平（不调用 API）。"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from cdxml_parser.text_ai.schema import (
    TABLE_HEADERS,
    flatten_to_tables,
    validate_compound_response,
)

FIXTURES = Path(__file__).resolve().parent / "fixtures" / "text_ai"


@pytest.mark.parametrize(
    "name",
    ["HW180002", "HW180003", "HW181079"],
)
def test_fixture_validate_and_flatten(name: str) -> None:
    raw = json.loads((FIXTURES / f"{name}.json").read_text(encoding="utf-8"))
    validate_compound_response(raw)
    tables = flatten_to_tables(
        [{"compound_id": raw["compound_id"], "parsed": raw, "error": None}]
    )
    assert len(tables["ic50"]) >= 1
    for table_name, headers in TABLE_HEADERS.items():
        for row in tables[table_name]:
            assert set(row.keys()) == set(headers)


def test_hw180002_ic50_rows() -> None:
    raw = json.loads((FIXTURES / "HW180002.json").read_text(encoding="utf-8"))
    tables = flatten_to_tables(
        [{"compound_id": "HW180002", "parsed": raw, "error": None}]
    )
    ic50 = tables["ic50"]
    assert any(r["Cell_line"] == "HEK293T" and r["IC50(nM)"] == "45.51" for r in ic50)
    assert any(r["Cell_line"] == "MCF-7" and r["Top（%）"] == "79.88" for r in ic50)
    assert len(tables["fu"]) == 5
    assert len(tables["cyp_inhibition"]) == 4


def test_hw180003_h226_continuation() -> None:
    raw = json.loads((FIXTURES / "HW180003.json").read_text(encoding="utf-8"))
    tables = flatten_to_tables(
        [{"compound_id": "HW180003", "parsed": raw, "error": None}]
    )
    h226 = [r for r in tables["ic50"] if r["Cell_line"] == "H226"]
    assert len(h226) >= 10
    assert len(tables["auc"]) == 3


def test_hw181079_stereochemistry() -> None:
    raw = json.loads((FIXTURES / "HW181079.json").read_text(encoding="utf-8"))
    tables = flatten_to_tables(
        [{"compound_id": "HW181079", "parsed": raw, "error": None}]
    )
    stereo = [r for r in tables["ic50"] if r.get("构型")]
    assert len(stereo) >= 1
    assert len(tables["mms"]) == 5
    assert tables["mms"][0]["检测方法"] == "肝微粒体"
