"""批量 AI 解析：并发、缓存、重试。"""

from __future__ import annotations

import hashlib
import json
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

from cdxml.text_ai.client import AiClientError, OpenAiCompatibleClient
from cdxml.text_ai.parser import parse_compound_with_ai
from cdxml.text_ai.schema import flatten_to_tables

LogFn = Callable[..., None]


def _default_log(*_args: object) -> None:
    pass


def _emit_progress(
    log: LogFn,
    *,
    done: int,
    total: int,
    compound_id: str,
    status: str,
) -> None:
    """向 stderr 打一行机器可读进度（Electron 解析）；人类日志仍走 log。"""
    line = json.dumps(
        {
            "type": "progress",
            "done": done,
            "total": total,
            "compound_id": compound_id,
            "status": status,
        },
        ensure_ascii=False,
    )
    log(line)


def _cache_path(config: Dict[str, Any]) -> Optional[Path]:
    p = (config.get("cache_dir") or "").strip()
    if p:
        return Path(p)
    return None


def _text_hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _load_cache(cache_dir: Path) -> Dict[str, Any]:
    f = cache_dir / "text_ai_cache.json"
    if not f.is_file():
        return {}
    try:
        return json.loads(f.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {}


def _save_cache(cache_dir: Path, cache: Dict[str, Any]) -> None:
    cache_dir.mkdir(parents=True, exist_ok=True)
    f = cache_dir / "text_ai_cache.json"
    f.write_text(json.dumps(cache, ensure_ascii=False, indent=2), encoding="utf-8")


def run_test_connection(config: Dict[str, Any]) -> Dict[str, Any]:
    try:
        client = OpenAiCompatibleClient(config)
        return client.test_connection()
    except AiClientError as e:
        return {"success": False, "message": str(e)}
    except Exception as e:
        return {"success": False, "message": f"{type(e).__name__}: {e}"}


def run_batch(
    config: Dict[str, Any],
    compounds: List[Dict[str, str]],
    *,
    log: LogFn = _default_log,
) -> Dict[str, Any]:
    """
    compounds: [{"compound_id": "...", "text": "..."}, ...]
    返回 batch 结果 JSON（含 tables、per_compound、统计）。
    """
    client = OpenAiCompatibleClient(config)
    try:
        client.ensure_configured()
    except AiClientError as e:
        return {
            "success": False,
            "message": str(e),
            "results": [],
            "tables": flatten_to_tables([]),
            "skipped_count": 0,
            "success_count": 0,
            "error_count": 0,
        }

    concurrency = max(1, int(config.get("concurrency", 3)))
    use_cache = bool(config.get("use_cache", True))
    cache_dir = _cache_path(config)
    cache: Dict[str, Any] = _load_cache(cache_dir) if (use_cache and cache_dir) else {}

    to_process: List[Dict[str, str]] = []
    results: List[Dict[str, Any]] = []
    skipped = 0
    total = len(compounds)
    done = 0

    for c in compounds:
        cid = (c.get("compound_id") or c.get("name") or "").strip()
        text = (c.get("text") or "").strip()
        if not text:
            skipped += 1
            results.append(
                {
                    "compound_id": cid,
                    "text": text,
                    "skipped": True,
                    "parsed": None,
                    "error": None,
                    "warnings": [],
                    "unparsed_lines": [],
                }
            )
            done += 1
            _emit_progress(log, done=done, total=total, compound_id=cid, status="skip")
            continue
        to_process.append({"compound_id": cid, "text": text})

    def work(item: Dict[str, str]) -> Dict[str, Any]:
        cid = item["compound_id"]
        text = item["text"]
        h = _text_hash(text)
        if use_cache and cache_dir and h in cache:
            log(f"[缓存] {cid}")
            parsed = cache[h]
            return {
                "compound_id": cid,
                "text": text,
                "skipped": False,
                "cached": True,
                "parsed": parsed,
                "error": None,
                "warnings": parsed.get("warnings") or [],
                "unparsed_lines": parsed.get("unparsed_lines") or [],
            }
        try:
            parsed = parse_compound_with_ai(client, cid, text)
            if use_cache and cache_dir is not None:
                cache[h] = parsed
            return {
                "compound_id": cid,
                "text": text,
                "skipped": False,
                "cached": False,
                "parsed": parsed,
                "error": None,
                "warnings": parsed.get("warnings") or [],
                "unparsed_lines": parsed.get("unparsed_lines") or [],
            }
        except Exception as e:
            return {
                "compound_id": cid,
                "text": text,
                "skipped": False,
                "cached": False,
                "parsed": None,
                "error": str(e),
                "warnings": [],
                "unparsed_lines": [],
            }

    # 合并已有 skipped 结果索引
    result_by_id = {r["compound_id"]: r for r in results}

    if total == 0:
        _emit_progress(log, done=0, total=0, compound_id="", status="ok")

    with ThreadPoolExecutor(max_workers=concurrency) as pool:
        futures = {pool.submit(work, item): item for item in to_process}
        for fut in as_completed(futures):
            item = futures[fut]
            res = fut.result()
            result_by_id[item["compound_id"]] = res
            done += 1
            if res.get("error"):
                prog_status = "fail"
                human = "FAIL"
            elif res.get("cached"):
                prog_status = "cache"
                human = "CACHE"
            else:
                prog_status = "ok"
                human = "OK"
            log(f"[{done}/{total}] {item['compound_id']}: {human}")
            _emit_progress(
                log,
                done=done,
                total=total,
                compound_id=item["compound_id"],
                status=prog_status,
            )

    if use_cache and cache_dir:
        _save_cache(cache_dir, cache)

    ordered: List[Dict[str, Any]] = []
    for c in compounds:
        cid = (c.get("compound_id") or c.get("name") or "").strip()
        ordered.append(result_by_id.get(cid, {"compound_id": cid, "error": "未处理"}))

    success_count = sum(1 for r in ordered if r.get("parsed") and not r.get("skipped"))
    error_count = sum(1 for r in ordered if r.get("error"))

    tables = flatten_to_tables(ordered)

    return {
        "success": error_count == 0 or success_count > 0,
        "message": f"完成：成功 {success_count}，失败 {error_count}，跳过空 text {skipped}",
        "results": ordered,
        "tables": tables,
        "skipped_count": skipped,
        "success_count": success_count,
        "error_count": error_count,
    }


def default_cache_dir() -> str:
    """Electron userData 或项目本地 .cache。"""
    env = os.environ.get("CDXML_AI_CACHE_DIR", "").strip()
    if env:
        return env
    return str(Path.cwd() / ".cache" / "text_ai")
