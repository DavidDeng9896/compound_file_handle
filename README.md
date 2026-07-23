# CDXML Compound Parser

从 ChemDraw 导出的 **CDXML** 中解析化合物结构（RDKit → SMILES），通过空间几何规则匹配 HW 编号、tPSA、CLogP 与其他说明文字，并导出 CSV。

详细算法与参数说明见 [docs/项目总结.md](docs/项目总结.md)。

## 目录结构

```
compound_file_handle/
├── cdxml/              # Python 核心包
│   ├── parser.py       # 解析与匹配
│   ├── bridge.py       # Electron 子进程桥接（JSON）
│   ├── text_ai_bridge.py  # AI 结构化 text 桥接
│   ├── text_ai/        # AI 解析 6 表 schema、批量、导出
│   ├── gui.py          # PySide6 图形界面
│   └── review.py       # 审查清单 CSV 导出
├── electron/           # Electron 桌面应用
├── packaging/          # PyInstaller 规格
├── scripts/            # 命令行工具脚本
├── samples/            # 示例 CDXML 与 CSV
├── docs/               # 项目文档
├── requirements.txt
└── build-release.cmd   # Windows 一键打包
```

## 快速开始

### 安装依赖

```bash
pip install -r requirements.txt
cd electron && npm install
```

### 命令行解析

```bash
python -m cdxml samples/cdxml/EO018\ compounds\ list.cdxml -o out.csv
```

### Electron 开发

```bash
cd electron && npm start
```

### PySide6 界面（可选）

```bash
pip install PySide6
python -m cdxml.gui
```

### 导出审查清单

```bash
python scripts/export_review.py samples/cdxml/EO018\ compounds\ list.cdxml -o review.csv
```

### AI 结构化 text（可选）

CDXML 解析完成后，在 Electron 界面展开 **「AI 结构化」**，配置 OpenAI 兼容 API（Base URL、Key、Model、提示词），点击 **「AI 结构化 text」** 将 `text` 拆为 6 张表并导出 CSV。

命令行（开发调试）：

```bash
# 测试 API 连接
echo {"config":{"api_key":"sk-..."}} | python -m cdxml.text_ai_bridge --test

# 批量结构化并导出 6 个 CSV
python scripts/parse_text_ai.py --config ai_config.json --input compounds.json -o out_structured/
```

配置保存在 Electron 用户目录 `ai_config.json`；也可用环境变量 `CDXML_AI_API_KEY` 覆盖 Key。

结构化输出表：`IC50`、`AUC0_t`、`Fu`、`Solubility`、`MMS_T12`、`CYP_inhibition`（字段定义见 `cdxml/text_ai/schema.py`）。

## 打包（Windows）

```bash
build-release.cmd
```

产出便携 exe：`electron/dist-installer/CDXML Compound Parser-*-portable-x64.exe`

## 匹配参数

| 参数 | 默认 | 说明 |
|------|------|------|
| `--match-x-left` | 0 | 结构框左侧 X 扩展（坐标单位） |
| `--match-x-right` | 0 | 结构框右侧 X 扩展 |
| `--match-y-down` | 130 | Y/距离匹配上限 |

Electron 桥接（开发态）：

```bash
python -m cdxml.bridge input.cdxml __NO_CSV__ 0 0 130
```

## 输出 CSV 列

`Compound_ID`, `structure`, `tPSA`, `CLogP`, `text`

示例格式见 [samples/compounds_list_template.csv](samples/compounds_list_template.csv)。
