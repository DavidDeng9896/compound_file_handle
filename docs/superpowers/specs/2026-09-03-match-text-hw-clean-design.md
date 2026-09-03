# 结构匹配：HW 编号清洗与其他文字 Y 区间归属

## 背景

1. HW 编号常带末尾括号备注，如 `HW1800023(VET,102354)`，需写入干净 ID。
2. 其他说明文字仅靠 `距离 < match_y_down` 易漏配或跨行误配；希望放大 `match_y_down` 时仍被「下方下一结构顶边」封顶。

## 决策（已确认）

| 项 | 选择 |
|----|------|
| 编号清洗 | 只去掉**末尾**一对圆括号及其中内容 |
| 下一结构 | 与当前结构 **X 重叠** 且中心 Y 更大、最近者 |
| 无下一结构 | 退回只用 `match_y_down` |
| Y 判定（仅其他文字） | 文字顶边中点 ∈ `[结构底边, min(底边+match_y_down, 下一结构顶边)]` |
| HW / tPSA / CLogP | **Y 规则不变** |
| 文字独占 | 每段其他文字只归一个结构；多候选取底边中点–顶边中点距离最近 |

## 设计

### 1. `strip_trailing_paren_group(s)`

- 匹配 `^(.*)(\([^)]*\))\s*$` 时去掉末尾括号组并 rstrip；否则原样返回。
- 分类仍用原文 `startswith("HW")`；清洗仅用于 `compound["name"]` / 导出 Compound_ID。

### 2. `find_next_structure_below(struct, structures, x_extend_*)`

- 在 `structures` 中找与当前结构 bbox X 重叠、且 `center_y` 严格更大者中 `center_y` 差最小的一个。
- 返回其 bbox（或结构引用）；没有则 `None`。

### 3. 其他文字归属（全局两阶段）

1. 对每个已匹配 compound，算 `upper = y2 + match_y_down`；若有 next，则 `upper = min(upper, next.y1)`。
2. 文字 T 对结构 S 可候选：X 重叠且 `S.y2 <= T.y1 <= upper`。
3. 每个 T 在全部候选中取距离最小的 S；按距离升序拼进该 S 的 `text`。

### 4. 不变

- X 扩展参数、HW/属性匹配、AI 六表逻辑不变。
- 默认 `match_y_down=130`；用户可自行调大。

## 测试

- 括号清洗单测
- 有/无下一结构的区间上界
- 大 `match_y_down` 不跨下一结构
- 并排多候选时独占最近结构
