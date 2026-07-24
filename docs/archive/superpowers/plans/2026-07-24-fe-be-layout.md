# FE/BE Layout Reorg Implementation Plan

> **For agentic workers:** Execute task-by-task. Steps use checkbox syntax.

**Goal:** Restructure repo into `frontend/` + `backend/` (all Python including restored tests); rename package `cdxml` → `cdxml_parser`.

**Architecture:** Backend workspace at `backend/` with `app/` (FastAPI), `cdxml_parser/`, `config/`, `tests/`. Frontend is renamed `web/` → `frontend/`. Samples stay at repo root.

**Tech Stack:** Python/FastAPI, Vue3/Vite, pytest

## Global Constraints

- Run API/CLI/tests from `backend/` with `PYTHONPATH=.`
- Import rename: `cdxml` → `cdxml_parser` everywhere
- Do not change parser/UI behavior
- Branch: `cursor/cleanup-unused-e631`

---

### Task 1: Move directories and restore tests

**Files:** move `cdxml`→`backend/cdxml_parser`, `server`→`backend/app`, `web`→`frontend`, restore tests→`backend/tests`, config→`backend/config`

- [ ] Create `backend/`, `git mv` packages, restore tests from `origin/main`, rename `app.py`→`main.py`
- [ ] Commit: `refactor: move code into frontend/ and backend/`

### Task 2: Rename imports and fix paths

**Files:** all Python under `backend/`, `scripts/dev.sh`, root requirements

- [ ] Replace `cdxml` imports with `cdxml_parser`
- [ ] Fix `app/main.py` ROOT/CONFIG paths to `backend/config/`
- [ ] Add `backend/requirements.txt` (merge root+server), root README points to backend
- [ ] Commit: `refactor: rename cdxml to cdxml_parser and fix backend paths`

### Task 3: Scripts, docs, gitignore

- [ ] Replace `scripts/dev-web.sh` with `scripts/dev.sh`
- [ ] Update README + `docs/项目总结.md`; archive `docs/superpowers` → `docs/archive/superpowers`
- [ ] Update `.gitignore` for `frontend/`, `backend/`
- [ ] Commit: `docs: update paths for FE/BE layout`

### Task 4: Verify

- [ ] `cd backend && PYTHONPATH=. pytest tests/ -q`
- [ ] `cd backend && PYTHONPATH=. python -c "from app.main import app; from cdxml_parser.parser import main"`
- [ ] Optional smoke: start uvicorn briefly
- [ ] Push and update PR
