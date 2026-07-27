# vxe-table 替换设计

**日期**: 2026-07-24  
**分支**: `cursor/biaoge-zujian-genghuan-e631`  
**状态**: 已确认（可编辑范围 = 方案 2）

## 目标

- 四个数据 Tab 的列表由 Element Plus `el-table` 换成 **vxe-table**
- 视觉对齐现有 `cf-table`（表头底、边框、字号、行距、悬停色、圆角）
- **仅**「化合物结构解析结果」「结构化数据表」支持双击单元格编辑
- 「未匹配结构」「解析失败文本」只读展示
- 结构预览列继续用 `StructureCell`；双击改 SMILES 后刷新结构图

## 技术选型

- `vxe-table`（Vue 3）+ `xe-utils`
- `edit-config.trigger = 'dblclick'`，`mode = 'cell'`
- 用 CSS 变量覆盖 vxe 主题，贴近 `--cf-*`

## 数据可变性

- 解析结果写入可编辑的 `ref` 列表（非只读 computed），导出 CSV 读最新值
- 结构化合并行同理；Compound_ID 合并逻辑在编辑后按需重算 rowspan

## 非目标

- 不改后端 API
- 不改匹配/AI 算法
- 不引入服务端保存编辑结果
