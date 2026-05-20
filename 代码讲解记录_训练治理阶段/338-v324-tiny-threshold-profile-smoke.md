# v324 tiny threshold profile smoke

## 本版目标和边界

v323 已经把第一个 threshold-blocked candidate 的分数、阈值和 margin 提到顶层 summary。v324 继续增强这个诊断，但仍然不扩展训练功能：它把 threshold blocker 从单点信息扩展成 profile。

本版目标：

- 统计因为 rubric threshold 被 blocked 的 candidate 数量。
- 输出这些 candidate 的名称列表。
- 找出最接近通过阈值的 candidate 和 margin。
- 找出离阈值差距最大的 candidate 和 margin。

边界：

- 不改 `benchmark_scorecard_decision.py` 的规则。
- 不改 scorecard scoring。
- 不改 tiny train/eval 参数。
- 不把 tiny smoke 的结果解释为真实模型能力结论。

## 前置能力

本版基于：

- v322 的 configurable decision threshold。
- v323 的 first threshold blocker diagnostics。
- 既有 tiny comparison smoke 顶层 summary JSON/text。

v324 的价值在于：当未来 comparison 不止一个 candidate 时，CI 不只知道第一个被挡住，还能知道整个 threshold blocker 集合的规模和分布。

## 关键文件

- `scripts/run_tiny_scorecard_comparison_smoke.py`
  - 新增 `threshold_blocks()`，把所有 rubric threshold blocker 投影为结构化行。
  - 新增 `threshold_block_profile()`，计算 count、names、closest 和 largest gap。
  - `decision_summary()` 新增 `threshold_*` 字段。
  - `render_summary()` 新增 `decision_threshold_*` 文本输出。

- `tests/test_tiny_scorecard_comparison_smoke.py`
  - 直接 summary 测试新增两个 threshold-blocked candidates。
  - 断言 `threshold_blocked_candidate_count=2`。
  - 断言 closest candidate 是 margin 较接近 0 的候选。
  - 断言 largest gap candidate 是 margin 最负的候选。
  - 真实 smoke 测试断言单 candidate profile 仍能正确输出。

- `README.md`
  - 当前版本更新到 v324。
  - benchmark/model comparison 能力补充 threshold profile counts/closest/largest-gap fields。

- `d/324`
  - 保存聚焦测试和真实 threshold profile summary 截图。

## 核心数据结构

v324 在 `scorecard_decision` summary 中新增：

```json
{
  "threshold_blocked_candidate_count": 1,
  "threshold_blocked_candidate_names": ["tiny-candidate"],
  "threshold_closest_candidate": "tiny-candidate",
  "threshold_closest_margin": -23.33,
  "threshold_largest_gap_candidate": "tiny-candidate",
  "threshold_largest_gap_margin": -23.33
}
```

字段含义：

- `threshold_blocked_candidate_count`
  - 因 `rubric_avg_score below ...` 被 blocked 的非 baseline candidate 数量。
- `threshold_blocked_candidate_names`
  - 对应 candidate 名称列表。
- `threshold_closest_candidate`
  - margin 最大的 threshold-blocked candidate，也就是最接近通过的候选。
- `threshold_closest_margin`
  - 最接近通过候选的 `rubric_score - threshold`。
- `threshold_largest_gap_candidate`
  - margin 最小的 threshold-blocked candidate，也就是离门槛最远的候选。
- `threshold_largest_gap_margin`
  - 离门槛最远候选的差距。

文本 summary 对应：

```text
decision_threshold_blocked_count=1
decision_threshold_blocked_candidates=tiny-candidate
decision_threshold_closest_candidate=tiny-candidate
decision_threshold_closest_margin=-23.33
decision_threshold_largest_gap_candidate=tiny-candidate
decision_threshold_largest_gap_margin=-23.33
```

## 运行流程

v324 不改变主流程，只增加 decision summary 的派生 profile：

```text
candidate_evaluations
  -> blocked nonbaseline rows
  -> threshold_blocks()
  -> threshold_block_profile()
  -> summary JSON/text
```

`threshold_blocks()` 只识别以 `rubric_avg_score below` 开头的 blocker，因此不会把 baseline blocker、overall regression 或 generation-quality review 项误算进去。

## 输入输出

输入：

- `benchmark_scorecard_decision.json`
- `min_rubric_score`
- `candidate_evaluations[*].blockers`
- `candidate_evaluations[*].rubric_avg_score`

输出：

- `tiny_scorecard_comparison_smoke_summary.json`
- `tiny_scorecard_comparison_smoke_summary.txt`

这些输出是只读 evidence summary，不是新的 benchmark 评分，也不是训练结果。

## 测试覆盖

聚焦测试：

```text
python -B -m unittest tests.test_tiny_scorecard_comparison_smoke -v
```

覆盖点：

- 没有 threshold blocker 时 count 为 0，names 为空，closest/largest gap 为 `None`。
- 两个 threshold blockers 时，count 和 names 正确。
- closest candidate 选择 margin 更接近 0 的候选。
- largest gap candidate 选择 margin 最负的候选。
- 真实 tiny smoke 输出 `decision_threshold_blocked_count=1` 和 closest candidate。

## 运行证据

归档位置：

```text
d/324/图片
d/324/解释/说明.md
```

截图证明：

- 聚焦测试通过。
- 真实 smoke summary 展示 threshold profile 字段。
- summary JSON 中也保留机器可读 profile。

## 一句话总结

v324 把 tiny threshold 诊断从“第一个 blocker”扩展为“blocked candidate profile”，让 CI 和人工审阅能判断阻断规模和差距分布。
