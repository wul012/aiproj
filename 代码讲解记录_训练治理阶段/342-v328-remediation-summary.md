# v328 remediation summary

## 本版目标和边界

v327 已经让 decision artifact 输出 `remediation_plan`。v328 不继续扩展新的失败类别，而是把 plan 的关键信息提升到 summary 层，让 CI、README 截图和人工审阅不用展开完整表格也能知道当前最主要的处理方向。

本版目标：

- decision summary 输出 remediation plan 总数。
- decision summary 输出 blocker/review remediation 分布。
- decision summary 输出 dominant remediation kind/category/action。
- tiny scorecard comparison smoke 顶层 summary 转述这些字段。
- Markdown summary 显示 remediation 概览。

边界：

- 不改变 promotion decision 规则。
- 不改变 scorecard scoring、threshold profile 或 taxonomy 分类。
- 不删除 v327 的完整 remediation plan 表格。

## 前置能力

本版基于 v326-v327：

```text
failure taxonomy
  -> remediation_plan[]
  -> remediation summary
  -> tiny smoke summary
```

v328 的价值是降低 review 成本，让报告既保留完整 action table，也有顶层摘要。

## 关键文件

- `src/minigpt/benchmark_scorecard_decision.py`
  - 新增 `_remediation_summary()`。
  - `build_benchmark_scorecard_decision()` 在生成 plan 后，把 summary 与 remediation summary 合并。
  - 新字段包括 `remediation_plan_count`、`remediation_blocker_count`、`remediation_review_count`、`dominant_remediation_kind`、`dominant_remediation_category`、`dominant_remediation_action`。

- `src/minigpt/benchmark_scorecard_decision_artifacts.py`
  - Markdown summary 新增 remediation count 和 dominant remediation 字段。

- `scripts/run_tiny_scorecard_comparison_smoke.py`
  - `decision_summary()` 转述 remediation summary。
  - `render_summary()` 输出 `decision_remediation_plan_count`、`decision_remediation_blocker_count`、`decision_remediation_review_count` 和 `decision_dominant_remediation_*`。

- `tests/test_benchmark_scorecard_decision.py`
  - 覆盖 remediation plan count、blocker/review count 和 dominant remediation。

- `tests/test_tiny_scorecard_comparison_smoke.py`
  - 覆盖 tiny smoke 顶层 summary 的 remediation summary 字段。

## 数据结构

summary 新增字段：

```json
{
  "remediation_plan_count": 1,
  "remediation_blocker_count": 1,
  "remediation_review_count": 0,
  "dominant_remediation_kind": "blocker",
  "dominant_remediation_category": "threshold",
  "dominant_remediation_action": "Improve the candidate rubric score before promotion, or lower the threshold only with an explicit policy change."
}
```

tiny smoke 文本新增：

```text
decision_remediation_plan_count=1
decision_remediation_blocker_count=1
decision_remediation_review_count=0
decision_dominant_remediation_category=threshold
```

## 运行流程

```text
summary category counts
  -> remediation_plan[]
  -> remediation_summary
  -> decision JSON/Markdown
  -> tiny smoke summary
```

remediation summary 是可读性和机器消费增强，不参与候选选择。

## 测试覆盖

聚焦测试：

```text
python -B -m unittest tests.test_benchmark_scorecard_decision tests.test_tiny_scorecard_comparison_smoke -v
```

覆盖点：

- plan 数量与 blocker/review 分布。
- dominant remediation kind/category/action。
- Markdown summary 输出。
- tiny smoke summary 输出。

## 运行证据

归档位置：

```text
d/328/图片
d/328/解释/说明.md
```

截图证明：

- 聚焦测试通过。
- tiny smoke summary 输出 remediation summary。
- decision Markdown 渲染 remediation summary。
- decision JSON 保存机器可读 summary。

## 一句话总结

v328 把 remediation plan 从详细表格提升到 summary 层，让失败处理建议更适合 CI 扫描和人工快速审阅。
