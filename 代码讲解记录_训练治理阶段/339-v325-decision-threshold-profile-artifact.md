# v325 decision threshold profile artifact

## 本版目标和边界

v324 已经让 tiny scorecard comparison smoke 顶层 summary 展示 threshold profile。问题是：profile 当时主要在 smoke wrapper 层计算，而真正的 `benchmark_scorecard_decision.json` 还没有把它作为正式决策摘要。

v325 的目标是把 profile 下沉到 decision artifact：

- `benchmark_scorecard_decision.py` 在 summary 中生成 threshold profile。
- `benchmark_scorecard_decision_artifacts.py` 在 Markdown/HTML 中渲染 profile。
- `run_tiny_scorecard_comparison_smoke.py` 优先消费 decision summary 中的 profile。
- wrapper 只保留旧 artifact 兼容回退。

边界：

- 不改 promotion decision 规则。
- 不改 scorecard scoring。
- 不改训练或 eval suite。
- 不把 tiny smoke blocked 结果解释为模型能力结论。

## 前置能力

本版基于：

- v322 的 configurable decision threshold。
- v323 的 first threshold blocker diagnostics。
- v324 的 top-level threshold profile。

v325 解决的是证据权威来源问题：profile 应该属于 decision artifact，因为 threshold blocker 是 promotion decision 的一部分，而不是 smoke wrapper 的私有摘要。

## 关键文件

- `src/minigpt/benchmark_scorecard_decision.py`
  - `_summary()` 接收 `min_rubric_score`。
  - 新增 `_threshold_blocks()`、`_threshold_profile()`、`_first_matching_list_item()`。
  - summary 新增 first threshold blocker 和 threshold profile 字段。
  - profile 只统计非 baseline rows，避免 baseline 的低分误入 promotion candidate 诊断。

- `src/minigpt/benchmark_scorecard_decision_artifacts.py`
  - Markdown 新增 threshold-blocked candidates、blocked names、closest 和 largest gap。
  - HTML stats card 新增 threshold blocked、threshold closest、threshold largest gap。
  - 新增 `_format_pair()` 用于 `candidate / margin` 展示。

- `scripts/run_tiny_scorecard_comparison_smoke.py`
  - `decision_summary()` 优先读取 decision summary 中的 threshold profile。
  - 若旧 decision artifact 没有这些字段，再回退到 wrapper 层计算。

- `tests/test_benchmark_scorecard_decision.py`
  - comparison fixture 支持额外 threshold-blocked candidate。
  - 新增 decision summary profile 测试。
  - 断言 JSON summary、Markdown、HTML 都包含 threshold profile。

- `tests/test_tiny_scorecard_comparison_smoke.py`
  - 继续覆盖 smoke 消费 profile 的 top-level summary 输出。

## 核心数据结构

decision summary 新增字段：

```json
{
  "first_threshold_blocked_candidate": "candidate",
  "first_threshold_blocker": "rubric_avg_score below 85.0",
  "first_threshold_rubric_score": 84.0,
  "first_threshold_min_rubric_score": 85.0,
  "first_threshold_margin": -1.0,
  "threshold_blocked_candidate_count": 2,
  "threshold_blocked_candidate_names": ["candidate", "candidate-far"],
  "threshold_closest_candidate": "candidate",
  "threshold_closest_margin": -1.0,
  "threshold_largest_gap_candidate": "candidate-far",
  "threshold_largest_gap_margin": -33.0
}
```

这组字段进入：

- decision JSON
- decision Markdown
- decision HTML stats cards
- tiny smoke top-level summary

## 运行流程

v325 的新流程是：

```text
scorecard comparison
  -> build_benchmark_scorecard_decision()
     -> candidate_evaluations
     -> _threshold_blocks(nonbaseline, min_rubric_score)
     -> _threshold_profile()
     -> report.summary
  -> decision artifacts
  -> tiny smoke summary consumes report.summary
```

如果旧的 decision artifact 没有 profile 字段，tiny smoke 会继续用 wrapper 层 helper 回退计算，这样不会破坏旧产物兼容。

## 输入输出

输入：

- scorecard comparison JSON。
- `min_rubric_score`。
- candidate evaluation rows。

输出：

- `benchmark_scorecard_decision.json`
- `benchmark_scorecard_decision.md`
- `benchmark_scorecard_decision.html`
- tiny smoke summary JSON/text。

这些输出是决策证据，不是训练结果，也不是模型质量证明。

## 测试覆盖

聚焦测试：

```text
python -B -m unittest tests.test_benchmark_scorecard_decision tests.test_tiny_scorecard_comparison_smoke -v
```

覆盖点：

- 两个 non-baseline threshold blockers 时，count、names、closest、largest gap 正确。
- baseline 的 threshold blocker 不进入 profile。
- Markdown 渲染 threshold-blocked count、closest 和 largest gap。
- HTML stats cards 渲染 threshold profile。
- tiny smoke summary 继续输出 `decision_threshold_*` 字段。

## 运行证据

归档位置：

```text
d/325/图片
d/325/解释/说明.md
```

截图证明：

- 聚焦测试通过。
- tiny smoke summary 消费 decision profile。
- decision Markdown 渲染 profile。
- decision JSON 保留机器可读 profile。

## 一句话总结

v325 把 threshold profile 从 smoke wrapper 的派生摘要提升为 benchmark scorecard decision artifact 的正式证据结构。
