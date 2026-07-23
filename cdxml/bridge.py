"""
供 Electron 子进程调用：stderr 输出运行日志，stdout 仅输出一行 JSON（解析结果）。

用法: python -m cdxml.bridge <输入.cdxml> <输出.csv|__NO_CSV__> [左扩展] [右扩展] [Y向下匹配]
     第二项为 __NO_CSV__ 时不写 CSV，仅返回 JSON（Electron 解析流程）。
     后三项可选，默认 0、0、130。
"""

from __future__ import annotations

import contextlib
import io
import json
import sys


def _configure_stdio_utf8() -> None:
    """Windows 下控制台常为 GBK，管道被 Electron 按 UTF-8 读取会乱码；统一为 UTF-8 输出。"""
    for name in ("stdout", "stderr"):
        stream = getattr(sys, name, None)
        if stream is None or not hasattr(stream, "buffer"):
            continue
        enc = (getattr(stream, "encoding", None) or "").lower()
        if enc in ("utf-8", "utf8"):
            continue
        setattr(
            sys,
            name,
            io.TextIOWrapper(
                stream.buffer,
                encoding="utf-8",
                errors="replace",
                line_buffering=(name == "stderr"),
            ),
        )


def _run() -> None:
    _configure_stdio_utf8()
    if len(sys.argv) < 3:
        err = {
            "success": False,
            "message": "用法: python -m cdxml.bridge <cdxml路径> <输出csv路径|__NO_CSV__>",
            "log_lines": [],
            "compounds": [],
        }
        print(json.dumps(err, ensure_ascii=False))
        sys.exit(1)

    cdxml_path = sys.argv[1]
    raw_output = sys.argv[2]
    skip_csv = raw_output in frozenset({"__NO_CSV__", "-"})
    output_path = None if skip_csv else raw_output
    match_x_extend_left = 0.0
    match_x_extend_right = 0.0
    match_y_down = 130.0
    if len(sys.argv) >= 4:
        try:
            match_x_extend_left = float(sys.argv[3])
        except ValueError:
            pass
    if len(sys.argv) >= 5:
        try:
            match_x_extend_right = float(sys.argv[4])
        except ValueError:
            pass
    if len(sys.argv) >= 6:
        try:
            match_y_down = float(sys.argv[5])
        except ValueError:
            pass
    log_lines: list[str] = []

    def log(*args: object) -> None:
        s = " ".join(str(a) for a in args)
        log_lines.append(s)
        print(s, file=sys.stderr)

    try:
        from cdxml.parser import main, parse_result_to_json_dict

        # 避免 RDKit/解析过程中的 print 污染 stdout（JSON）
        with contextlib.redirect_stdout(sys.stderr):
            result = main(
                cdxml_path,
                output_path,
                log=log,
                match_x_extend_left=match_x_extend_left,
                match_x_extend_right=match_x_extend_right,
                match_y_down=match_y_down,
            )

        payload = parse_result_to_json_dict(result, log_lines=log_lines)
        print(json.dumps(payload, ensure_ascii=False))
    except Exception as e:
        payload = {
            "success": False,
            "message": f"{type(e).__name__}: {e}",
            "compound_count": 0,
            "output_csv_path": output_path or "",
            "log_lines": log_lines,
            "compounds": [],
            "unmatched_hw": [],
            "unmatched_structures": [],
            "unused_property_texts": [],
            "unused_other_texts": [],
            "matched_but_empty_smiles": [],
        }
        print(json.dumps(payload, ensure_ascii=False))
        sys.exit(1)


if __name__ == "__main__":
    _run()
