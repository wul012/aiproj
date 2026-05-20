# v330 remediation CSV artifact

## 本版目标和边界

v329 已经让 remediation plan 带上 action code、severity、owner scope 和 target artifacts。v330 不再继续增加字段，而是把这份 plan 单独写成 CSV artifact，降低后续 CI、表格工具和脚本消费成本。

本版目标：

- 新增 `benchmark_scorecard_decision_remediation.csv`。
- `write_benchmark_scorecard_decision_outputs()` 返回 `remediation_csv` 路径。
- tiny scorecard comparison smoke artifact status 检查 remediation CSV。
- 测试覆盖 CSV 表头、内容和 smoke 产物存在性。

边界：

- 不改变 remediation plan 的 JSON 结构。
- 不改变 Markdown/HTML 展示语义。
- 不改变 decision 规则、训练、评分或 threshold profile。

## 前置能力

本版基于：

```text
v327 remediation_plan[]
  -> v328 remediation summary
  -> v329 remediation metadata
  -> v330 remediation CSV artifact
```

CSV 是额外出口，不替代 JSON。

## 关键文件

- `src/minigpt/benchmark_scorecard_decision_artifacts.py`
  - 新增 `write_benchmark_scorecard_remediation_csv()`。
  - `write_benchmark_scorecard_decision_outputs()` 新增 `remediation_csv`。
  - CSV 字段为 `kind/category/count/priority/severity/owner_scope/action_code/target_artifacts/action`。

- `src/minigpt/benchmark_scorecard_decision.py`
  - re-export `write_benchmark_scorecard_remediation_csv()`，保持 facade 使用方式一致。

- `scripts/run_tiny_scorecard_comparison_smoke.py`
  - artifact status 新增 `decision_remediation_csv_path` 和 `decision_remediation_csv_exists`。

- `tests/test_benchmark_scorecard_decision.py`
  - 覆盖 writer re-export。
  - 覆盖 outputs key 中新增 `remediation_csv`。
  - 覆盖 threshold remediation CSV 中的 action code 和 target artifacts。

- `tests/test_tiny_scorecard_comparison_smoke.py`
  - 覆盖真实 tiny smoke 生成 remediation CSV。
  - 覆盖 artifact status 中 remediation CSV 存在。

## 输出格式

CSV 表头：

```text
kind,category,count,priority,severity,owner_scope,action_code,target_artifacts,action
```

threshold 行示例：

```text
blocker,threshold,1,60,blocker,model-eval,raise_candidate_rubric_or_change_policy,benchmark_scorecard_decision; benchmark_scorecard,...
```

`target_artifacts` 继续沿用仓库已有 list CSV 表达方式，用 `; ` 拼接。

## 运行流程

```text
build decision report
  -> remediation_plan[]
  -> write JSON/CSV/Markdown/HTML
  -> write remediation CSV
  -> tiny smoke artifact status
```

remediation CSV 是 evidence artifact，不参与候选选择。

## 测试覆盖

聚焦测试：

```text
python -B -m unittest tests.test_benchmark_scorecard_decision tests.test_tiny_scorecard_comparison_smoke -v
```

覆盖点：

- facade re-export。
- outputs key。
- remediation CSV 表头。
- remediation CSV 内容。
- tiny smoke artifact status。

## 运行证据

归档位置：

```text
d/330/图片
d/330/解释/说明.md
```

截图证明：

- 聚焦测试通过。
- smoke artifact status 显示 remediation CSV 存在。
- remediation CSV 内容包含 action code 和 target artifacts。
- Markdown remediation table 仍保留。

## 一句话总结

v330 把 remediation plan 从 JSON/Markdown/HTML 中的内容进一步导出为独立 CSV artifact，让行动项更容易进入 CI、表格分析和后续自动化。
