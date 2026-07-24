"""6 表 CSV 导出。"""

from __future__ import annotations

import csv
import io
from pathlib import Path
from typing import Dict, List

from cdxml.text_ai.schema import CSV_FILENAMES, TABLE_HEADERS, TABLE_NAMES

BOM = "\ufeff"


def _rows_to_csv_string(headers: List[str], rows: List[Dict[str, str]]) -> str:
    buf = io.StringIO()
    buf.write(BOM)
    writer = csv.DictWriter(buf, fieldnames=headers, lineterminator="\n", extrasaction="ignore")
    writer.writeheader()
    for row in rows:
        writer.writerow({h: row.get(h, "") for h in headers})
    return buf.getvalue()


def tables_to_csv_dict(tables: Dict[str, List[Dict[str, str]]]) -> Dict[str, str]:
    out: Dict[str, str] = {}
    for name in TABLE_NAMES:
        headers = TABLE_HEADERS[name]
        rows = tables.get(name) or []
        out[CSV_FILENAMES[name]] = _rows_to_csv_string(headers, rows)
    return out


def export_tables_to_dir(tables: Dict[str, List[Dict[str, str]]], out_dir: str | Path) -> List[str]:
    path = Path(out_dir)
    path.mkdir(parents=True, exist_ok=True)
    written: List[str] = []
    for name, csv_name in CSV_FILENAMES.items():
        fp = path / csv_name
        content = tables_to_csv_dict(tables)[csv_name]
        fp.write_text(content, encoding="utf-8")
        written.append(str(fp))
    return written
