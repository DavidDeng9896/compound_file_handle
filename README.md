# CDXML Compound Parser

从 ChemDraw 导出的 **CDXML** 中解析化合物结构（RDKit → SMILES），通过空间几何规则匹配 HW 编号、tPSA、CLogP 与其他说明文字，并导出 CSV。可选对 `text` 做 AI 结构化拆表。

详细算法与参数说明见 [docs/项目总结.md](docs/项目总结.md)。

## 目录结构

```
compound_file_handle/
├── cdxml/              # Python 核心包
│   ├── parser.py       # 解析与匹配
│   └── text_ai/        # AI 解析 schema、批量、导出、连表合并
├── server/             # FastAPI Web API
├── web/                # Vue3 + Element Plus 前端
├── scripts/
│   └── dev-web.sh      # 一键启动 API + Vite
├── samples/            # 示例 CDXML 与 CSV
├── docs/               # 项目文档
└── requirements.txt
```

## 快速开始

### 安装依赖

```bash
pip install -r requirements.txt
cd web && npm install && cd ..
```

### Web UI（推荐）

```bash
# 终端 1：API
PYTHONPATH=. uvicorn server.app:app --reload --host 0.0.0.0 --port 8000
# 终端 2：前端
cd web && npm run dev
```

浏览器打开 Vite 提示的地址（默认 http://127.0.0.1:5173）。

或一键：

```bash
./scripts/dev-web.sh
```

### 命令行解析

```bash
python -m cdxml samples/cdxml/EO018\ compounds\ list.cdxml -o out.csv
```

可选匹配参数：`--match-x-left`、`--match-x-right`、`--match-y-down`。

### AI 结构化 text

在 Web UI 中配置 OpenAI 兼容 API（Base URL、Key、Model、提示词），解析完成后对 `text` 做结构化拆表。

也可将配置放在本地 `ai_config.json`（见 `ai_config.example.json`；该文件已 gitignore），或用环境变量 `CDXML_AI_API_KEY` 覆盖 Key。

结构化输出表：`IC50`、`AUC0_t`、`Fu`、`Solubility`、`MMS_T12`、`CYP_inhibition`（字段定义见 `cdxml/text_ai/schema.py`）。

## 匹配参数

| 参数 | 默认 | 说明 |
|------|------|------|
| `--match-x-left` | 0 | 结构框左侧 X 扩展（坐标单位） |
| `--match-x-right` | 0 | 结构框右侧 X 扩展 |
| `--match-y-down` | 130 | Y/距离匹配上限 |

## 输出 CSV 列

`Compound_ID`, `structure`, `tPSA`, `CLogP`, `text`

示例格式见 [samples/compounds_list_template.csv](samples/compounds_list_template.csv)。
