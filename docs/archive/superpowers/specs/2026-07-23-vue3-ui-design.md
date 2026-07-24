# 化合物解析 Vue3 UI 调整设计

## 目标

按《化合物插件功能及UI调整》效果图，用 **Vue 3 + Element Plus** 重建界面；开发/测试用普通 Web 服务启动，不依赖 Electron。

## 架构

- **前端** `web/`：Vite + Vue 3 + Element Plus + smiles-drawer
- **后端** `server/`：FastAPI，复用现有 `cdxml.parser` / `cdxml.text_ai`，提供上传、解析、AI 结构化、配置与导出 API
- **Electron 壳保留**：后续可再接同一套前端构建产物；本次不以 Electron 启动验证

## UI（对齐效果图）

1. **主布局**：标题「化合物解析」；上传 CDXML；右侧入口「结构匹配设置」「AI 解析设置」；操作区「开始解析 / 文本解析 / 自动执行」+ AI 进度；提示文案；四 Tab；底栏日志与导出/导入
2. **设置**：默认收起；点击后右侧 Drawer 浮层（匹配参数 / AI 配置）
3. **Tab 仅保留**：解析结果、未匹配结构、结构化数据表、解析失败文本
4. **结构化数据表**：按 `Compound_ID` 多表横向合并（见下）

## 结构化合并规则

- 主键：`Compound_ID`
- 同一 ID 多条记录占多行，不丢弃重复
- 各表同一 ID 的第 N 条记录横向对齐到同一行
- 行数 = 该 ID 在各表中的最大条数；较短表对应单元格留空
- 表头两级：表名 + 原字段（不含重复的 Compound_ID 子列）

## API（概要）

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/parse` | 上传 CDXML + 匹配参数 → 解析结果 JSON |
| POST | `/api/text-ai` | compounds + AI 配置 → 结构化 tables（SSE 进度） |
| GET/POST | `/api/ai-config` | 读写 AI 配置 |
| POST | `/api/export/*` | 导出 CSV 文本 |

## 自动执行

依次：结构解析 →（过滤无法解析结构/空 SMILES）→ 文本 AI 结构化。
