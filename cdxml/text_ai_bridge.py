"""
供 Electron 子进程调用：stdin JSON → stdout 一行 JSON。

用法:
  echo {...} | python -m cdxml.text_ai_bridge
  python -m cdxml.text_ai_bridge --test < config.json
"""

from __future__ import annotations

import contextlib
import io
import json
import sys
from typing import Any, Dict

from cdxml.text_ai.batch import default_cache_dir, run_batch, run_test_connection


def _configure_stdio_utf8() -> None:
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


def _read_stdin_json() -> Dict[str, Any]:
    raw = sys.stdin.read()
    if not raw.strip():
        return {}
    return json.loads(raw)


def _emit(payload: Dict[str, Any]) -> None:
    print(json.dumps(payload, ensure_ascii=False))


def _run_test(config: Dict[str, Any]) -> None:
    result = run_test_connection(config)
    _emit(result)
    if not result.get("success"):
        sys.exit(1)


def _run_batch_mode(body: Dict[str, Any]) -> None:
    config = body.get("config") or {}
    compounds = body.get("compounds") or []
    if not config.get("cache_dir"):
        config = dict(config)
        config["cache_dir"] = default_cache_dir()

    log_lines: list[str] = []

    def log(*args: object) -> None:
        s = " ".join(str(a) for a in args)
        log_lines.append(s)
        print(s, file=sys.stderr)

    with contextlib.redirect_stdout(sys.stderr):
        payload = run_batch(config, compounds, log=log)
    payload["log_lines"] = log_lines
    _emit(payload)
    if not payload.get("success"):
        sys.exit(1)


def main() -> None:
    _configure_stdio_utf8()
    if len(sys.argv) >= 2 and sys.argv[1] == "--test":
        try:
            body = _read_stdin_json()
            _run_test(body.get("config") or body)
        except Exception as e:
            _emit({"success": False, "message": f"{type(e).__name__}: {e}"})
            sys.exit(1)
        return

    try:
        body = _read_stdin_json()
        if body.get("mode") == "test":
            _run_test(body.get("config") or {})
            return
        _run_batch_mode(body)
    except json.JSONDecodeError as e:
        _emit({"success": False, "message": f"stdin JSON 无效: {e}", "results": [], "tables": {}})
        sys.exit(1)
    except Exception as e:
        _emit({"success": False, "message": f"{type(e).__name__}: {e}", "results": [], "tables": {}})
        sys.exit(1)


if __name__ == "__main__":
    main()
