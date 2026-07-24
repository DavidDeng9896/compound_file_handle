"""AI 解析化合物 text 字段为结构化实验数据表。"""

from cdxml_parser.text_ai.batch import run_batch, run_test_connection
from cdxml_parser.text_ai.export_csv import export_tables_to_dir, tables_to_csv_dict
from cdxml_parser.text_ai.schema import flatten_to_tables, validate_compound_response

__all__ = [
    "flatten_to_tables",
    "validate_compound_response",
    "export_tables_to_dir",
    "tables_to_csv_dict",
    "run_batch",
    "run_test_connection",
]
