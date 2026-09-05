# 结构优先文字匹配 Implementation Plan

> **For agentic workers:** 按任务顺序 TDD 实现；每步可独立验证。

**Goal:** 将 CDXML 匹配改为结构优先，并在匹配内做类型独占去重，消除重复 HW 抢结构这类问题。

**Architecture:** 候选边 `(structure, text, dist)` + 按距离贪心独占；HW/属性用附近区，其他文字用向下 Y 带。

**Tech Stack:** Python、pytest、现有 `cdxml_parser.parser`

## Global Constraints

- 默认 `match_y_down=300`；X 扩展语义不变
- 只输出认领到 HW 的结构
- 中文日志风格与现有一致

---

### Task 1: 独占分配工具函数 + 单测

**Files:**
- Modify: `backend/cdxml_parser/parser.py`
- Modify: `backend/tests/test_parser_match.py`

- [ ] 新增 `assign_texts_exclusively(...)`（结构侧每类上限、文字侧全局一次）
- [ ] 新增 `text_in_structure_near_zone(...)`（HW/属性附近区）
- [ ] 单测：重合双 HW 只给上结构；同一文字不双分
- [ ] Commit

### Task 2: 主流程改为结构优先

**Files:**
- Modify: `backend/cdxml_parser/parser.py`

- [ ] `main()`：按结构生成 HW 候选并独占认领，再认领 tPSA/CLogP/other
- [ ] 移除「每个 HW 抢结构」主循环
- [ ] EO035 回归：HW356041 / HW356047
- [ ] 全量 pytest
- [ ] Commit / 更新 PR
