# 前后端分离目录整理设计

**日期**: 2026-07-24  
**状态**: 已实施（branch `cursor/cleanup-unused-e631`）

## 目标

将仓库整理为清晰的 **前端 / 后端** 分离结构：

- 全部 Python（API、解析库、CLI、测试）归入 `backend/`
- Vue 前端归入 `frontend/`
- 核心包更名为 `cdxml_parser`（原 `cdxml`）
- **恢复** 原 `tests/` 内容，迁入 `backend/tests/`（清理 PR 中删除的用例一并找回）

## 目标目录树

```text
compound_file_handle/
├── README.md
├── .gitignore
│
├── frontend/                         # 原 web/
│   ├── package.json
│   ├── vite.config.js                # /api → 后端 :8000
│   ├── index.html
│   ├── public/
│   └── src/
│
├── backend/                          # 全部 Python
│   ├── pyproject.toml                # 统一依赖（可保留 requirements.txt 兼容）
│   ├── app/                          # FastAPI
│   │   ├── __init__.py
│   │   └── main.py                   # uvicorn backend.app.main:app
│   ├── cdxml_parser/                 # 原 cdxml/
│   │   ├── __init__.py
│   │   ├── __main__.py               # python -m cdxml_parser
│   │   ├── parser.py
│   │   └── text_ai/
│   ├── config/
│   │   └── ai_config.example.json
│   └── tests/                        # 原根目录 tests/（恢复并改 import）
│       ├── fixtures/text_ai/
│       ├── test_text_ai_*.py
│       └── ...
│
├── samples/                          # 示例 CDXML/CSV（前后端共用，留根目录）
├── scripts/
│   └── dev.sh                        # 启动 API + Vite
│
└── docs/
    ├── 项目总结.md
    └── archive/                      # 可选：原 docs/superpowers 过程文档
```

## 映射关系

| 现在 | 整理后 |
|------|--------|
| `web/` | `frontend/` |
| `server/` | `backend/app/` |
| `cdxml/` | `backend/cdxml_parser/` |
| 根 `tests/`（已删，从 git 恢复） | `backend/tests/` |
| `ai_config.example.json` | `backend/config/ai_config.example.json` |
| `scripts/dev-web.sh` | `scripts/dev.sh` |
| `docs/superpowers/` | `docs/archive/superpowers/`（可选归档） |

## 运行约定

```bash
# 安装后端（在仓库根或 backend 下）
pip install -e backend

# 开发一键启动
./scripts/dev.sh
# API:  http://127.0.0.1:8000
# Web:  http://127.0.0.1:5173  （proxy /api → 8000）

# CLI
cd backend && python -m cdxml_parser path/to/file.cdxml -o out.csv

# 测试
cd backend && pytest tests/
```

- `uvicorn` 模块路径：`backend.app.main:app`（需保证仓库根在 `PYTHONPATH`，或通过 editable install 暴露包）。
- 实施时二选一并写死在文档：**(推荐)** 根目录 `PYTHONPATH=.` + 包布局使 `backend` 为顶层包；或 editable install 后调整为 `app.main:app`。为减少歧义，推荐结构为：

  - 物理路径：`backend/app/main.py`、`backend/cdxml_parser/`
  - 启动：`cd backend && PYTHONPATH=. uvicorn app.main:app`
  - CLI / pytest 均在 `backend/` 工作目录下执行

  这样 **不必** 把 `backend` 本身当成 Python 包名，目录即工作区，更直观。

## Import 变更

- 所有 `from cdxml...` / `import cdxml` → `cdxml_parser`
- 测试、API、`__main__`、文档示例同步更新
- 前端仅改目录名与 `dev.sh` 中的路径；业务代码尽量不动（仍 `/api`）

## 非目标

- 不引入 monorepo `apps/` + `packages/` 双层
- 不把 `samples/` 强行搬进 backend（示例数据前后端共用，留根）
- 不在本任务中改 UI 行为或解析算法

## 验收

- [ ] `frontend` / `backend` 目录边界清晰，根目录无散落 Python 包
- [ ] `python -m cdxml_parser` 可解析示例 CDXML
- [ ] `uvicorn app.main:app`（在 `backend/` 下）可启动 API
- [ ] `frontend` `npm run dev` 可代理调用 API
- [ ] `backend/tests` 原有用例恢复且全部通过（import 已改为 `cdxml_parser`）
- [ ] README / 项目总结路径与命令已更新
