"""
CDXML 化合物解析 — 图形界面：主结果 CSV + 未匹配/待复核项表格与导出。
"""

from __future__ import annotations

import sys
from pathlib import Path

from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtGui import QAction
from PySide6.QtWidgets import (
    QApplication,
    QFileDialog,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPlainTextEdit,
    QPushButton,
    QSplitter,
    QTabWidget,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from cdxml.parser import ParseResult, main
from cdxml.review import export_review_csv


def _float_cell(v: float) -> QTableWidgetItem:
    it = QTableWidgetItem(f"{v:.2f}")
    it.setFlags(it.flags() & ~Qt.ItemFlag.ItemIsEditable)
    return it


def _text_cell(s: str) -> QTableWidgetItem:
    it = QTableWidgetItem(s)
    it.setFlags(it.flags() & ~Qt.ItemFlag.ItemIsEditable)
    return it


def fill_table_hw(table: QTableWidget, rows: list) -> None:
    table.clearContents()
    table.setRowCount(len(rows))
    headers = ["HW 文字", "X1", "Y1", "X2", "Y2", "中心 X", "中心 Y"]
    table.setColumnCount(len(headers))
    table.setHorizontalHeaderLabels(headers)
    for i, r in enumerate(rows):
        table.setItem(i, 0, _text_cell(r.get("content", "")))
        table.setItem(i, 1, _float_cell(r["x1"]))
        table.setItem(i, 2, _float_cell(r["y1"]))
        table.setItem(i, 3, _float_cell(r["x2"]))
        table.setItem(i, 4, _float_cell(r["y2"]))
        table.setItem(i, 5, _float_cell(r["center_x"]))
        table.setItem(i, 6, _float_cell(r["center_y"]))


def fill_table_struct(table: QTableWidget, rows: list) -> None:
    table.clearContents()
    table.setRowCount(len(rows))
    headers = ["结构序号", "SMILES", "X1", "Y1", "X2", "Y2", "中心 X", "中心 Y"]
    table.setColumnCount(len(headers))
    table.setHorizontalHeaderLabels(headers)
    for i, r in enumerate(rows):
        table.setItem(i, 0, _text_cell(str(r.get("structure_index", ""))))
        table.setItem(i, 1, _text_cell(r.get("smiles", "") or ""))
        table.setItem(i, 2, _float_cell(r["x1"]))
        table.setItem(i, 3, _float_cell(r["y1"]))
        table.setItem(i, 4, _float_cell(r["x2"]))
        table.setItem(i, 5, _float_cell(r["y2"]))
        table.setItem(i, 6, _float_cell(r["center_x"]))
        table.setItem(i, 7, _float_cell(r["center_y"]))


def fill_table_text_rows(table: QTableWidget, rows: list, label: str) -> None:
    table.clearContents()
    table.setRowCount(len(rows))
    headers = [label, "X1", "Y1", "X2", "Y2", "中心 X", "中心 Y"]
    table.setColumnCount(len(headers))
    table.setHorizontalHeaderLabels(headers)
    for i, r in enumerate(rows):
        table.setItem(i, 0, _text_cell(r.get("content", "")))
        table.setItem(i, 1, _float_cell(r["x1"]))
        table.setItem(i, 2, _float_cell(r["y1"]))
        table.setItem(i, 3, _float_cell(r["x2"]))
        table.setItem(i, 4, _float_cell(r["y2"]))
        table.setItem(i, 5, _float_cell(r["center_x"]))
        table.setItem(i, 6, _float_cell(r["center_y"]))


def fill_table_empty_smiles(table: QTableWidget, rows: list) -> None:
    table.clearContents()
    table.setRowCount(len(rows))
    headers = ["Compound_ID", "X1", "Y1", "X2", "Y2", "中心 X", "中心 Y"]
    table.setColumnCount(len(headers))
    table.setHorizontalHeaderLabels(headers)
    for i, r in enumerate(rows):
        table.setItem(i, 0, _text_cell(r.get("Compound_ID", "")))
        table.setItem(i, 1, _float_cell(r["x1"]))
        table.setItem(i, 2, _float_cell(r["y1"]))
        table.setItem(i, 3, _float_cell(r["x2"]))
        table.setItem(i, 4, _float_cell(r["y2"]))
        table.setItem(i, 5, _float_cell(r["center_x"]))
        table.setItem(i, 6, _float_cell(r["center_y"]))


def fill_table_empty_smiles(table: QTableWidget, rows: list) -> None:
    finished_ok = Signal(object, str)
    failed = Signal(str)

    def __init__(self, cdxml_path: str, output_csv: str) -> None:
        super().__init__()
        self._cdxml_path = cdxml_path
        self._output_csv = output_csv

    def run(self) -> None:
        lines: list[str] = []

        def log(*args: object, **kwargs: object) -> None:
            lines.append(" ".join(str(a) for a in args))

        try:
            result = main(self._cdxml_path, self._output_csv, log=log)
            self.finished_ok.emit(result, "\n".join(lines))
        except Exception as e:
            self.failed.emit(f"{type(e).__name__}: {e}")


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("CDXML 化合物解析工具")
        self.resize(1100, 720)
        self._last_result: ParseResult | None = None

        central = QWidget()
        self.setCentralWidget(central)
        root = QVBoxLayout(central)

        row_in = QHBoxLayout()
        row_in.addWidget(QLabel("CDXML 文件:"))
        self.edit_cdxml = QLineEdit()
        row_in.addWidget(self.edit_cdxml, 1)
        btn_in = QPushButton("浏览…")
        btn_in.clicked.connect(self._pick_cdxml)
        row_in.addWidget(btn_in)
        root.addLayout(row_in)

        row_out = QHBoxLayout()
        row_out.addWidget(QLabel("输出 CSV:"))
        self.edit_csv = QLineEdit()
        row_out.addWidget(self.edit_csv, 1)
        btn_out = QPushButton("浏览…")
        btn_out.clicked.connect(self._pick_csv)
        row_out.addWidget(btn_out)
        root.addLayout(row_out)

        row_run = QHBoxLayout()
        self.btn_run = QPushButton("开始解析")
        self.btn_run.clicked.connect(self._run_parse)
        row_run.addWidget(self.btn_run)
        self.btn_export_review = QPushButton("导出审查清单 CSV…")
        self.btn_export_review.setEnabled(False)
        self.btn_export_review.clicked.connect(self._export_review)
        row_run.addWidget(self.btn_export_review)
        row_run.addStretch(1)
        self.status = QLabel("")
        row_run.addWidget(self.status)
        root.addLayout(row_run)

        splitter = QSplitter(Qt.Orientation.Vertical)
        self.log_view = QPlainTextEdit()
        self.log_view.setReadOnly(True)
        self.log_view.setPlaceholderText("运行日志将显示在此处…")
        splitter.addWidget(self.log_view)

        self.tabs = QTabWidget()
        self.table_hw = QTableWidget()
        self.table_struct = QTableWidget()
        self.table_prop = QTableWidget()
        self.table_other = QTableWidget()
        self.table_empty_smiles = QTableWidget()
        for t in (
            self.table_hw,
            self.table_struct,
            self.table_prop,
            self.table_other,
            self.table_empty_smiles,
        ):
            t.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
            t.horizontalHeader().setStretchLastSection(True)
            t.setAlternatingRowColors(True)

        self.tabs.addTab(self.table_hw, "未匹配 HW 文字")
        self.tabs.addTab(self.table_struct, "未匹配结构")
        self.tabs.addTab(self.table_prop, "未使用的 tPSA/CLogP 行")
        self.tabs.addTab(self.table_other, "未匹配的其他文字")
        self.tabs.addTab(self.table_empty_smiles, "已匹配但 SMILES 为空")
        splitter.addWidget(self.tabs)
        splitter.setSizes([280, 440])
        root.addWidget(splitter, 1)

        bar = self.menuBar().addMenu("帮助")
        act_about = QAction("关于", self)
        act_about.triggered.connect(self._about)
        bar.addAction(act_about)

    def _pick_cdxml(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self, "选择 CDXML", "", "ChemDraw XML (*.cdxml);;所有文件 (*.*)"
        )
        if path:
            self.edit_cdxml.setText(path)
            p = Path(path)
            self.edit_csv.setText(str(p.with_name(p.stem + "_compounds.csv")))

    def _pick_csv(self) -> None:
        path, _ = QFileDialog.getSaveFileName(
            self, "保存 CSV", "", "CSV (*.csv);;所有文件 (*.*)"
        )
        if path:
            self.edit_csv.setText(path)

    def _about(self) -> None:
        QMessageBox.about(
            self,
            "关于",
            "CDXML 化合物解析工具\n\n"
            "从 ChemDraw CDXML 提取 HW 编号、SMILES 与属性，生成主结果 CSV；\n"
            "未匹配项在下方各页签中列出，可导出审查清单 CSV。",
        )

    def _run_parse(self) -> None:
        cdxml = self.edit_cdxml.text().strip()
        out = self.edit_csv.text().strip()
        if not cdxml:
            QMessageBox.warning(self, "提示", "请选择 CDXML 文件。")
            return
        if not out:
            QMessageBox.warning(self, "提示", "请指定输出 CSV 路径。")
            return
        if not Path(cdxml).is_file():
            QMessageBox.warning(self, "提示", "CDXML 文件不存在。")
            return

        self.btn_run.setEnabled(False)
        self.btn_export_review.setEnabled(False)
        self.status.setText("解析中…")
        self.log_view.clear()
        self._clear_tables()

        self._worker = ParseWorker(cdxml, out)
        self._worker.finished_ok.connect(self._on_parse_done)
        self._worker.failed.connect(self._on_parse_fail)
        self._worker.start()

    def _clear_tables(self) -> None:
        for t in (
            self.table_hw,
            self.table_struct,
            self.table_prop,
            self.table_other,
            self.table_empty_smiles,
        ):
            t.setRowCount(0)
            t.setColumnCount(0)

    def _on_parse_done(self, result: ParseResult, log_text: str) -> None:
        self.btn_run.setEnabled(True)
        self._last_result = result
        self.log_view.setPlainText(log_text)

        if not result.success:
            self.status.setText(result.message or "失败")
            QMessageBox.warning(self, "解析失败", result.message or "未知错误")
            return

        self.status.setText(
            f"完成：{result.compound_count} 条化合物 → {Path(result.output_csv_path).name}"
        )
        self.btn_export_review.setEnabled(True)

        fill_table_hw(self.table_hw, result.unmatched_hw)
        fill_table_struct(self.table_struct, result.unmatched_structures)
        fill_table_text_rows(self.table_prop, result.unused_property_texts, "tPSA/CLogP 行")
        fill_table_text_rows(self.table_other, result.unused_other_texts, "其他文字")
        fill_table_empty_smiles(self.table_empty_smiles, result.matched_but_empty_smiles)

        # 摘要写入日志末尾
        extra = (
            f"\n\n--- 审查摘要 ---\n"
            f"未匹配 HW 文字: {len(result.unmatched_hw)}\n"
            f"未匹配结构: {len(result.unmatched_structures)}\n"
            f"未使用的 tPSA/CLogP 行: {len(result.unused_property_texts)}\n"
            f"未匹配的其他文字: {len(result.unused_other_texts)}\n"
            f"已匹配但 SMILES 为空: {len(result.matched_but_empty_smiles)}"
        )
        self.log_view.appendPlainText(extra)

    def _on_parse_fail(self, msg: str) -> None:
        self.btn_run.setEnabled(True)
        self.status.setText("出错")
        self.log_view.appendPlainText(msg)
        QMessageBox.critical(self, "解析异常", msg)

    def _export_review(self) -> None:
        if self._last_result is None or not self._last_result.success:
            return
        path, _ = QFileDialog.getSaveFileName(
            self, "导出审查清单 CSV", "", "CSV (*.csv);;所有文件 (*.*)"
        )
        if not path:
            return
        try:
            export_review_csv(path, self._last_result)
        except OSError as e:
            QMessageBox.critical(self, "保存失败", str(e))
            return
        QMessageBox.information(self, "已保存", f"审查清单已保存到:\n{path}")


def main_gui() -> None:
    app = QApplication(sys.argv)
    w = MainWindow()
    w.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main_gui()
