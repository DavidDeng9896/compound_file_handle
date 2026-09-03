# CDXML Compound Parser

从 ChemDraw 导出的 **CDXML** 中解析化合物结构（RDKit → SMILES），通过空间几何规则匹配 HW 编号、tPSA、CLogP 与其他说明文字，并导出 CSV。可选对 `text` 做 AI 结构化拆表。

- **功能说明**（已实现能力）：[docs/功能说明.md](docs/功能说明.md)
- **算法与参数**：[docs/项目总结.md](docs/项目总结.md)

## 目录结构

```
compound_file_handle/
├── frontend/              # Vue3 + Element Plus + Vite
├── backend/               # 全部 Python
│   ├── app/               # FastAPI（uvicorn app.main:app）
│   ├── cdxml_parser/      # 解析核心 + text_ai + CLI
│   ├── config/            # ai_config.example.json 等
│   ├── tests/             # pytest
│   └── requirements.txt
├── samples/               # 示例 CDXML 与 CSV
├── scripts/
│   └── dev.sh             # 一键启动 API + Vite
├── docs/
└── requirements.txt       # 转发到 backend/requirements.txt
```

## 快速开始

### 安装依赖

```bash
pip install -r requirements.txt
cd frontend && npm install && cd ..
```

### Web UI（推荐）

```bash
./scripts/dev.sh
```

浏览器打开 http://127.0.0.1:5173（Vite 将 `/api` 代理到后端 `:8000`）。

需要外网访问时，另开终端：

```bash
./scripts/tunnel.sh
```

终端会打印 `https://*.trycloudflare.com` 公网地址（需本机已安装 `cloudflared`）。

手动启动：

```bash
# 终端 1：API（在 backend 目录）
cd backend
PYTHONPATH=. uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# 终端 2：前端
cd frontend && npm run dev
```

### 命令行解析

```bash
cd backend
PYTHONPATH=. python -m cdxml_parser ../samples/cdxml/EO018\ compounds\ list.cdxml -o out.csv
```

可选匹配参数：`--match-x-left`、`--match-x-right`、`--match-y-down`。

### AI 结构化 text

在 Web UI 中配置 OpenAI 兼容 API。也可将配置放在 `backend/config/ai_config.json`（见 `backend/config/ai_config.example.json`；该文件已 gitignore），或用环境变量 `CDXML_AI_API_KEY` 覆盖 Key。

结构化输出表：`IC50`、`AUC0_t`、`Fu`、`Solubility`、`MMS_T12`、`CYP_inhibition`（字段定义见 `backend/cdxml_parser/text_ai/schema.py`）。

## 匹配参数

| 参数 | 默认 | 说明 |
|------|------|------|
| `--match-x-left` | 0 | 结构框左侧 X 扩展（坐标单位） |
| `--match-x-right` | 0 | 结构框右侧 X 扩展 |
| `--match-y-down` | 300 | Y/距离匹配上限 |

## 输出 CSV 列

`Compound_ID`, `structure`, `tPSA`, `CLogP`, `text`

示例格式见 [samples/compounds_list_template.csv](samples/compounds_list_template.csv)。

## 测试

```bash
cd backend
PYTHONPATH=. pytest tests/
```
