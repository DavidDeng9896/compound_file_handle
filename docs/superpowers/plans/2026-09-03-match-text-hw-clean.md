# HW 清洗与文字 Y 区间归属 Implementation Plan

> **For agentic workers:** Implement task-by-task. Steps use checkbox syntax.

**Goal:** 清洗 HW 末尾括号；其他说明文字用「match_y_down ∩ 下一结构顶边」区间归属，且一段文字只归一个结构。

**Architecture:** 在 `parser.py` 抽出纯函数（清洗 / 下一结构 / Y 区间），其他文字改为化合物匹配完成后的全局独占分配；HW/tPSA/CLogP 保持原 Y 逻辑。

**Tech Stack:** Python、pytest、现有 `cdxml_parser.parser`

## Global Constraints

- 不改 AI text_ai schema/prompts
- HW/tPSA/CLogP 的 Y 匹配规则不变
- 分支名：`cursor/match-text-hw-clean-e631`

---

### Task 1: 纯函数 + 单测

**Files:**
- Modify: `backend/cdxml_parser/parser.py`
- Create: `backend/tests/test_parser_match.py`

- [ ] 实现 `strip_trailing_paren_group`、`find_next_structure_below`、`other_text_in_y_band`
- [ ] 单测覆盖清洗、有/无 next、区间边界、X 重叠选 next
- [ ] Commit

### Task 2: 接入 `main` 匹配流程

**Files:**
- Modify: `backend/cdxml_parser/parser.py`
- Modify: `backend/tests/test_parser_match.py`

- [ ] `name` 写入时清洗括号
- [ ] 其他文字改为全局独占分配（距底边中点最近）
- [ ] 集成向单测（合成 bbox 列表驱动辅助函数或轻量入口）
- [ ] Commit

### Task 3: 文档与 PR

**Files:**
- Modify: `docs/项目总结.md`、`docs/功能说明.md`（若有匹配说明）

- [ ] 同步算法说明
- [ ] 推送并开 PR
