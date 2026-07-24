"""tests for Compound_ID table merge."""

from cdxml_parser.text_ai.merge import merge_tables_by_compound_id
from cdxml_parser.text_ai.schema import flatten_to_tables
import json
from pathlib import Path


FIXTURE = Path(__file__).parent / "fixtures" / "text_ai" / "HW180002.json"


def test_merge_aligns_nth_records_horizontally():
    tables = {
        "ic50": [
            {"Compound_ID": "A", "Cell_line": "c1", "IC50(nM)": "1", "IC50_SD": "", "Top（%）": "", "Positive control": "", "构型": ""},
            {"Compound_ID": "A", "Cell_line": "c2", "IC50(nM)": "2", "IC50_SD": "", "Top（%）": "", "Positive control": "", "构型": ""},
        ],
        "auc": [
            {"Compound_ID": "A", "Species": "mouse", "AUC₀₋t（h·ng/mL）": "10", "F%": "", "给药剂量(mpk)": ""},
        ],
        "fu": [],
        "solubility": [],
        "mms": [],
        "cyp_inhibition": [],
    }
    rows, cols = merge_tables_by_compound_id(tables)
    assert len(rows) == 2
    assert rows[0]["Compound_ID"] == "A"
    assert rows[0]["ic50__Cell_line"] == "c1"
    assert rows[0]["auc__Species"] == "mouse"
    assert rows[1]["ic50__Cell_line"] == "c2"
    assert rows[1]["auc__Species"] == ""
    assert cols[0]["prop"] == "Compound_ID"
    assert any(c["label"] == "ic50" for c in cols)


def test_merge_keeps_duplicate_compound_ids_as_multiple_rows():
    tables = {
        "ic50": [
            {"Compound_ID": "X", "Cell_line": "a", "IC50(nM)": "1", "IC50_SD": "", "Top（%）": "", "Positive control": "", "构型": ""},
            {"Compound_ID": "X", "Cell_line": "b", "IC50(nM)": "2", "IC50_SD": "", "Top（%）": "", "Positive control": "", "构型": ""},
            {"Compound_ID": "Y", "Cell_line": "c", "IC50(nM)": "3", "IC50_SD": "", "Top（%）": "", "Positive control": "", "构型": ""},
        ],
        "auc": [],
        "fu": [],
        "solubility": [],
        "mms": [],
        "cyp_inhibition": [],
    }
    rows, _ = merge_tables_by_compound_id(tables, compound_id_order=["X", "Y"])
    assert [r["Compound_ID"] for r in rows] == ["X", "X", "Y"]


def test_merge_fixture_hw180002_row_count():
    raw = json.loads(FIXTURE.read_text(encoding="utf-8"))
    tables = flatten_to_tables([{"compound_id": raw["compound_id"], "parsed": raw}])
    rows, _ = merge_tables_by_compound_id(tables)
    # max of table lengths for this compound
    expected = max(len(tables[k]) for k in tables)
    assert len(rows) == expected
    assert rows[0]["Compound_ID"] == "HW180002"
    assert rows[0]["ic50__Cell_line"] == "HEK293T"
