"""FastAPI web server for CDXML compound parser (non-Electron)."""

from __future__ import annotations

import csv
import io
import json
import os
import tempfile
import threading
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, File, Form, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel, Field

from cdxml.parser import main as parse_main, parse_result_to_json_dict
from cdxml.text_ai.batch import default_cache_dir, run_batch, run_test_connection
from cdxml.text_ai.export_csv import tables_to_csv_dict
from cdxml.text_ai.merge import merge_tables_by_compound_id
from cdxml.text_ai.prompts import DEFAULT_SYSTEM_PROMPT, DEFAULT_USER_PROMPT_TEMPLATE

ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = Path(os.environ.get("CDXML_AI_CONFIG", str(ROOT / "ai_config.json")))

DEFAULT_AI_CONFIG: Dict[str, Any] = {
    "base_url": "https://api.openai.com/v1",
    "api_key": "",
    "model": "gpt-4o-mini",
    "temperature": 0,
    "max_tokens": 4096,
    "concurrency": 3,
    "use_cache": True,
    "system_prompt": DEFAULT_SYSTEM_PROMPT,
    "user_prompt_template": DEFAULT_USER_PROMPT_TEMPLATE,
}

app = FastAPI(title="CDXML Compound Parser API", version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

_ai_lock = threading.Lock()


def _load_ai_config() -> Dict[str, Any]:
    cfg = dict(DEFAULT_AI_CONFIG)
    if CONFIG_PATH.is_file():
        try:
            saved = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
            if isinstance(saved, dict):
                cfg.update(saved)
        except (json.JSONDecodeError, OSError):
            pass
    env_key = os.environ.get("CDXML_AI_API_KEY", "").strip()
    if env_key:
        cfg["api_key"] = env_key
    return cfg


def _save_ai_config(config: Dict[str, Any]) -> Dict[str, Any]:
    merged = _load_ai_config()
    for k, v in config.items():
        if k == "api_key" and (v is None or v == ""):
            continue
        merged[k] = v
    CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    CONFIG_PATH.write_text(json.dumps(merged, ensure_ascii=False, indent=2), encoding="utf-8")
    return merged


def _public_ai_config(cfg: Dict[str, Any]) -> Dict[str, Any]:
    out = dict(cfg)
    key = out.get("api_key") or ""
    out["api_key_set"] = bool(key)
    out["api_key"] = "" if key else ""
    # 前端可显示是否已配置；不回传明文 key
    if key:
        out["api_key_masked"] = key[:4] + "****" + key[-4:] if len(key) > 8 else "****"
    return out


class AiConfigBody(BaseModel):
    base_url: Optional[str] = None
    api_key: Optional[str] = None
    model: Optional[str] = None
    concurrency: Optional[int] = None
    system_prompt: Optional[str] = None
    user_prompt_template: Optional[str] = None
    temperature: Optional[float] = None
    max_tokens: Optional[int] = None
    use_cache: Optional[bool] = None


class CompoundItem(BaseModel):
    compound_id: str = ""
    text: str = ""


class TextAiBody(BaseModel):
    compounds: List[CompoundItem] = Field(default_factory=list)
    config: Optional[AiConfigBody] = None
    exclude_empty_smiles: bool = False
    stream: bool = False


class ExportMainBody(BaseModel):
    compounds: List[Dict[str, Any]] = Field(default_factory=list)


class ExportStructuredBody(BaseModel):
    tables: Dict[str, List[Dict[str, Any]]] = Field(default_factory=dict)
    merged: bool = True
    compound_id_order: Optional[List[str]] = None


@app.get("/api/health")
def health() -> Dict[str, str]:
    return {"status": "ok"}


@app.get("/api/ai-config")
def get_ai_config() -> Dict[str, Any]:
    return _public_ai_config(_load_ai_config())


@app.post("/api/ai-config")
def save_ai_config(body: AiConfigBody) -> Dict[str, Any]:
    data = {k: v for k, v in body.model_dump().items() if v is not None}
    saved = _save_ai_config(data)
    return {"success": True, "config": _public_ai_config(saved)}


@app.post("/api/ai-config/test")
def test_ai_config(body: AiConfigBody | None = None) -> Dict[str, Any]:
    cfg = _load_ai_config()
    if body:
        patch = {k: v for k, v in body.model_dump().items() if v is not None}
        if patch.get("api_key") == "":
            patch.pop("api_key", None)
        cfg.update(patch)
    return run_test_connection(cfg)


@app.post("/api/parse")
async def parse_cdxml(
    file: UploadFile = File(...),
    match_x_extend_left: float = Form(0),
    match_x_extend_right: float = Form(0),
    match_y_down: float = Form(130),
) -> JSONResponse:
    suffix = Path(file.filename or "upload.cdxml").suffix or ".cdxml"
    log_lines: List[str] = []

    def log(*args: object) -> None:
        log_lines.append(" ".join(str(a) for a in args))

    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        content = await file.read()
        tmp.write(content)
        tmp_path = tmp.name

    try:
        result = parse_main(
            tmp_path,
            None,
            log=log,
            match_x_extend_left=float(match_x_extend_left),
            match_x_extend_right=float(match_x_extend_right),
            match_y_down=float(match_y_down),
        )
        payload = parse_result_to_json_dict(result, log_lines=log_lines)
        payload["filename"] = file.filename or ""
        return JSONResponse(payload)
    except Exception as e:
        return JSONResponse(
            {
                "success": False,
                "message": f"{type(e).__name__}: {e}",
                "compounds": [],
                "log_lines": log_lines,
            },
            status_code=500,
        )
    finally:
        try:
            os.unlink(tmp_path)
        except OSError:
            pass


def _merge_config(patch: Optional[AiConfigBody]) -> Dict[str, Any]:
    cfg = _load_ai_config()
    if patch:
        data = {k: v for k, v in patch.model_dump().items() if v is not None}
        if data.get("api_key") == "":
            data.pop("api_key", None)
        cfg.update(data)
    if not cfg.get("cache_dir"):
        cfg["cache_dir"] = str(default_cache_dir())
    return cfg


@app.post("/api/text-ai")
def text_ai(body: TextAiBody) -> Any:
    compounds = [c.model_dump() for c in body.compounds]
    if body.exclude_empty_smiles:
        compounds = [c for c in compounds if (c.get("text") or "").strip()]

    cfg = _merge_config(body.config)

    if body.stream:
        def event_gen():
            progress_buf: List[Dict[str, Any]] = []

            def log(*args: object) -> None:
                s = " ".join(str(a) for a in args)
                try:
                    obj = json.loads(s)
                    if isinstance(obj, dict) and obj.get("type") == "progress":
                        progress_buf.append(obj)
                        yield_line = f"data: {json.dumps(obj, ensure_ascii=False)}\n\n"
                        # store for outer — use list mutation
                        progress_buf[-1]["_sse"] = yield_line
                except (json.JSONDecodeError, TypeError):
                    pass

            # run_batch is sync; we emulate SSE by wrapping progress via queue
            from queue import Queue

            q: Queue = Queue()

            def log_q(*args: object) -> None:
                s = " ".join(str(a) for a in args)
                try:
                    obj = json.loads(s)
                    if isinstance(obj, dict) and obj.get("type") == "progress":
                        q.put(("progress", obj))
                        return
                except (json.JSONDecodeError, TypeError):
                    pass
                q.put(("log", s))

            result_holder: Dict[str, Any] = {}

            def worker() -> None:
                with _ai_lock:
                    result_holder["payload"] = run_batch(cfg, compounds, log=log_q)
                q.put(("done", None))

            t = threading.Thread(target=worker, daemon=True)
            t.start()
            while True:
                kind, data = q.get()
                if kind == "progress":
                    yield f"data: {json.dumps(data, ensure_ascii=False)}\n\n"
                elif kind == "log":
                    yield f"data: {json.dumps({'type': 'log', 'message': data}, ensure_ascii=False)}\n\n"
                elif kind == "done":
                    payload = result_holder.get("payload") or {}
                    order = [c.get("compound_id", "") for c in compounds]
                    merged_rows, col_defs = merge_tables_by_compound_id(
                        payload.get("tables") or {},
                        compound_id_order=order,
                    )
                    payload["merged_rows"] = merged_rows
                    payload["merged_columns"] = col_defs
                    yield f"data: {json.dumps({'type': 'result', 'payload': payload}, ensure_ascii=False)}\n\n"
                    break

        return StreamingResponse(event_gen(), media_type="text/event-stream")

    with _ai_lock:
        payload = run_batch(cfg, compounds, log=lambda *a: None)
    order = [c.get("compound_id", "") for c in compounds]
    merged_rows, col_defs = merge_tables_by_compound_id(
        payload.get("tables") or {},
        compound_id_order=order,
    )
    payload["merged_rows"] = merged_rows
    payload["merged_columns"] = col_defs
    return payload


@app.post("/api/merge-tables")
def merge_tables(body: ExportStructuredBody) -> Dict[str, Any]:
    rows, cols = merge_tables_by_compound_id(
        body.tables,
        compound_id_order=body.compound_id_order,
    )
    return {"merged_rows": rows, "merged_columns": cols}


@app.post("/api/export/main-csv")
def export_main_csv(body: ExportMainBody) -> Dict[str, str]:
    buf = io.StringIO()
    buf.write("\ufeff")
    writer = csv.writer(buf, lineterminator="\n")
    writer.writerow(["Compound_ID", "structure", "tPSA", "CLogP", "text"])
    for c in body.compounds:
        writer.writerow(
            [
                c.get("compound_id") or c.get("Compound_ID") or "",
                c.get("smiles") or c.get("structure") or "",
                c.get("tpsa") if c.get("tpsa") is not None else c.get("tPSA", ""),
                c.get("clogp") if c.get("clogp") is not None else c.get("CLogP", ""),
                c.get("text") or "",
            ]
        )
    return {"filename": "compounds.csv", "content": buf.getvalue()}


@app.post("/api/export/structured-csv")
def export_structured_csv(body: ExportStructuredBody) -> Dict[str, Any]:
    if body.merged:
        rows, cols = merge_tables_by_compound_id(
            body.tables,
            compound_id_order=body.compound_id_order,
        )
        headers: List[str] = []
        for g in cols:
            if not g.get("children"):
                headers.append(g["prop"])
            else:
                for ch in g["children"]:
                    headers.append(f"{g['label']}.{ch['label']}")
        props: List[str] = []
        for g in cols:
            if not g.get("children"):
                props.append(g["prop"])
            else:
                for ch in g["children"]:
                    props.append(ch["prop"])
        buf = io.StringIO()
        buf.write("\ufeff")
        writer = csv.writer(buf, lineterminator="\n")
        writer.writerow(headers)
        for row in rows:
            writer.writerow([row.get(p, "") for p in props])
        return {"filename": "structured_merged.csv", "content": buf.getvalue()}
    files = tables_to_csv_dict(body.tables)
    return {"files": files}
