# v327 decision remediation plan

## 本版目标和边界

v326 已经把 benchmark scorecard decision 的 blocker/review 文本分类成 taxonomy。v327 继续向前走一小步：把这些类别映射成结构化 remediation plan，让报告不只告诉审阅者“失败类型是什么”，也告诉审阅者“下一步应该处理什么”。

本版目标：

- decision JSON 输出 `remediation_plan`。
- Markdown 和 HTML 展示 remediation 表格。
- recommendations 追加最高优先级 remediation 的文字摘要。
- tiny scorecard comparison smoke 顶层 summary 转述 remediation count、first category 和 first action。

边界：

- 不改变 promotion decision 规则。
- 不改变模型训练、eval suite 或 benchmark scorecard scoring。
- 不把 tiny smoke 的 blocked 结果解释为模型能力结论。
- 不为干净 promote 场景渲染空 remediation 表。

## 前置能力

本版基于 v326 的 failure taxonomy：

```text
blockers/review_items
  -> blocker_categories/review_categories
  -> category counts
  -> dominant category
```

v327 新增的是：

```text
category counts
  -> remediation_plan[]
  -> report table
  -> tiny smoke top-level action
```

## 关键文件

- `src/minigpt/benchmark_scorecard_decision.py`
  - 新增 `BLOCKER_REMEDIATION_ACTIONS` 和 `REVIEW_REMEDIATION_ACTIONS`。
  - 新增 `_remediation_plan()`，从 summary 的 category counts 生成结构化 action 列表。
  - `build_benchmark_scorecard_decision()` 将 `remediation_plan` 写入顶层 JSON。
  - `_recommendations()` 追加 `Top remediation: category -> action`。

- `src/minigpt/benchmark_scorecard_decision_artifacts.py`
  - Markdown 新增 `## Remediation Plan` 表格。
  - HTML 新增 remediation plan table。
  - 当 plan 为空时不渲染空表。

- `scripts/run_tiny_scorecard_comparison_smoke.py`
  - `decision_summary()` 转述 remediation plan 的数量和第一条 action。
  - `render_summary()` 输出 `decision_remediation_count`、`decision_first_remediation_category`、`decision_first_remediation_action`。

- `tests/test_benchmark_scorecard_decision.py`
  - 断言 blocked/threshold 场景生成正确的 remediation plan。
  - 断言 Markdown 和 HTML 渲染 plan。
  - 断言 clean promote 场景仍保持报告简洁。

- `tests/test_tiny_scorecard_comparison_smoke.py`
  - 断言 tiny smoke 顶层 summary 转述 first remediation。

## 数据结构

decision JSON 顶层新增：

```json
{
  "remediation_plan": [
    {
      "kind": "blocker",
      "category": "threshold",
      "count": 1,
      "priority": 60,
      "action": "Improve the candidate rubric score before promotion, or lower the threshold only with an explicit policy change."
    }
  ]
}
```

tiny smoke text 新增：

```text
decision_remediation_count=1
decision_first_remediation_category=threshold
decision_first_remediation_action=Improve the candidate rubric score before promotion, or lower the threshold only with an explicit policy change.
```

## 运行流程

```text
candidate evaluation
  -> category counts
  -> remediation plan
  -> JSON/Markdown/HTML
  -> tiny smoke summary
```

remediation plan 是解释层和操作建议层，不参与 candidate 选择或阻断判定。

## 测试覆盖

聚焦测试：

```text
python -B -m unittest tests.test_benchmark_scorecard_decision tests.test_tiny_scorecard_comparison_smoke -v
```

覆盖点：

- blocker taxonomy 到 remediation plan 的映射。
- review taxonomy 到 remediation plan 的保留路径。
- plan 按 count 和 priority 排序。
- Markdown/HTML 只在 plan 非空时渲染表格。
- tiny smoke 顶层 summary 转述第一条 remediation。

## 运行证据

归档位置：

```text
d/327/图片
d/327/解释/说明.md
```

截图证明：

- 聚焦测试通过。
- tiny smoke summary 输出 remediation 字段。
- decision Markdown 渲染 remediation plan。
- decision JSON 保存机器可读 remediation plan。

## 一句话总结

v327 把 benchmark scorecard decision 的 failure taxonomy 扩展为 remediation plan，让 CI、报告和人工审阅都能直接看到下一步处理动作。
