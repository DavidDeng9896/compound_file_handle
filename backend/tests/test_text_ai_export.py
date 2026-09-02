"""export_csv 单元测试。"""

from cdxml_parser.text_ai.export_csv import tables_to_csv_dict
from cdxml_parser.text_ai.schema import flatten_to_tables
import json
from pathlib import Path

FIXTURES = Path(__file__).resolve().parent / "fixtures" / "text_ai"


def test_csv_dict_has_bom_and_headers() -> None:
    raw = json.loads((FIXTURES / "HW180002.json").read_text(encoding="utf-8"))
    tables = flatten_to_tables(
        [{"compound_id": "HW180002", "parsed": raw, "error": None}]
    )
    csv_map = tables_to_csv_dict(tables)
    assert "IC50.csv" in csv_map
    assert csv_map["IC50.csv"].startswith("\ufeff")
    assert "Compound_ID" in csv_map["IC50.csv"]
    assert "AUC₀₋t（h·ng/mL）" in csv_map["AUC0_t.csv"]
    assert "给药途径" in csv_map["AUC0_t.csv"]
