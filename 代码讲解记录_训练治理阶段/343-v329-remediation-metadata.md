# v329 remediation metadata

## 本版目标和边界

v327-v328 已经把 failure taxonomy 映射成 remediation plan，并把 plan 概览提升到 summary 层。v329 的目标是让每条 remediation 不只是自然语言建议，而是更像可分派、可脚本消费的行动项。

本版目标：

- 每条 remediation plan 增加 `action_code`。
- 每条 remediation plan 增加 `severity`。
- 每条 remediation plan 增加 `owner_scope`。
- 每条 remediation plan 增加 `target_artifacts`。
- Markdown/HTML 表格展示这些 metadata。
- tiny smoke 顶层 summary 转述第一条 remediation 的 action code、severity 和 owner scope。

边界：

- 不改变 taxonomy 分类规则。
- 不改变 remediation plan 排序规则。
- 不改变 promotion decision 规则。
- 不改变训练、eval suite 或 scorecard scoring。

## 前置能力

本版基于：

```text
v326 failure taxonomy
  -> v327 remediation plan
  -> v328 remediation summary
  -> v329 remediation metadata
```

v329 的作用是让下一步可以自然接入 dashboard、CI 或计划脚本，而不是继续依赖人工阅读长句。

## 关键文件

- `src/minigpt/benchmark_scorecard_decision.py`
  - 新增 `BLOCKER_REMEDIATION_METADATA`。
  - 新增 `REVIEW_REMEDIATION_METADATA`。
  - `_remediation_plan()` 为每个 action 写入 `action_code`、`severity`、`owner_scope`、`target_artifacts`。

- `src/minigpt/benchmark_scorecard_decision_artifacts.py`
  - Markdown remediation table 新增 `Severity`、`Owner`、`Action Code`、`Target Artifacts`。
  - HTML remediation table 同步展示这些列。

- `scripts/run_tiny_scorecard_comparison_smoke.py`
  - `decision_summary()` 转述第一条 remediation 的 action code、severity、owner scope。
  - `render_summary()` 输出 `decision_first_remediation_action_code`、`decision_first_remediation_severity`、`decision_first_remediation_owner_scope`。

- `tests/test_benchmark_scorecard_decision.py`
  - 覆盖 action code、severity、owner scope、target artifacts。
  - 覆盖 Markdown/HTML 表格列。

- `tests/test_tiny_scorecard_comparison_smoke.py`
  - 覆盖 tiny smoke 顶层 summary 中的 remediation metadata。

## 数据结构

remediation plan 示例：

```json
{
  "kind": "blocker",
  "category": "threshold",
  "count": 1,
  "priority": 60,
  "action_code": "raise_candidate_rubric_or_change_policy",
  "severity": "blocker",
  "owner_scope": "model-eval",
  "target_artifacts": ["benchmark_scorecard_decision", "benchmark_scorecard"],
  "action": "Improve the candidate rubric score before promotion, or lower the threshold only with an explicit policy change."
}
```

tiny smoke text 示例：

```text
decision_first_remediation_action_code=raise_candidate_rubric_or_change_policy
decision_first_remediation_severity=blocker
decision_first_remediation_owner_scope=model-eval
```

## 运行流程

```text
category counts
  -> remediation metadata lookup
  -> remediation_plan[]
  -> Markdown/HTML/JSON
  -> tiny smoke summary
```

metadata 是操作语义增强，不参与候选选择。

## 测试覆盖

聚焦测试：

```text
python -B -m unittest tests.test_benchmark_scorecard_decision tests.test_tiny_scorecard_comparison_smoke -v
```

覆盖点：

- threshold blocker 的 action code、severity、owner scope 和 target artifacts。
- rubric regression blocker 的 metadata。
- Markdown/HTML 表格展示 metadata 列。
- tiny smoke summary 转述第一条 remediation metadata。

## 运行证据

归档位置：

```text
d/329/图片
d/329/解释/说明.md
```

截图证明：

- 聚焦测试通过。
- tiny smoke 输出 first remediation metadata。
- Markdown remediation table 展示 action code/owner/target artifacts。
- JSON 保存机器可读 metadata。

## 一句话总结

v329 把 remediation plan 从自然语言建议升级为带 action code、severity、owner scope 和 target artifacts 的可执行行动项。
