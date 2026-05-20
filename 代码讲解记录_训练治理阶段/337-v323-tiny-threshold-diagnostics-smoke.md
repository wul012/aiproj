# v323 tiny threshold diagnostics smoke

## 本版目标和边界

v322 让 tiny scorecard comparison smoke 的 promotion threshold 从隐藏常量变成命令行配置。v323 继续沿着这个方向，把 threshold 阻断原因从 decision JSON 里提到顶层 summary。

本版目标：

- 找到第一个因为 `rubric_avg_score below ...` 被 blocked 的非 baseline candidate。
- 在 `scorecard_decision` summary 里记录 candidate 名称、rubric 分、配置阈值和差距。
- 在文本 summary 里输出同样字段，方便 CI 日志直接阅读。

边界：

- 不改 `benchmark_scorecard_decision.py` 的判断规则。
- 不改 benchmark scorecard 评分。
- 不改 tiny training 参数。
- 不把 tiny smoke 的 blocked/promote/review 解释成真实模型能力结论。

## 前置能力

本版依赖 v318-v322 已经建立的链路：

```text
tiny train
  -> eval suite
  -> generation quality
  -> benchmark scorecard
  -> scorecard comparison
  -> scorecard decision
  -> top-level smoke summary
```

v322 已经把 `--decision-min-rubric-score` 写入 run config。v323 补的是“诊断解释”：当候选没过这个阈值时，summary 直接说明差距。

## 关键文件

- `scripts/run_tiny_scorecard_comparison_smoke.py`
  - `decision_summary()` 新增 threshold blocker 提取。
  - `render_summary()` 新增四个文本字段。
  - 新增 `first_threshold_block()`、`first_matching_list_item()`、`float_or_none()` 小 helper。

- `tests/test_tiny_scorecard_comparison_smoke.py`
  - 新增 `decision_summary` 直接单元测试。
  - 真实 smoke 测试断言 threshold candidate、threshold min 和负 margin。
  - summary 渲染测试断言没有 threshold blocker 时输出 `None`。

- `README.md`
  - 当前版本更新到 v323。
  - benchmark/model comparison 能力补充 threshold blocker score/margin diagnostics。

- `d/323`
  - 保存聚焦测试和真实 threshold diagnostics summary 截图。

## 核心数据结构

v323 在 `scorecard_decision` summary 中新增：

```json
{
  "first_threshold_blocked_candidate": "tiny-candidate",
  "first_threshold_blocker": "rubric_avg_score below 60.0",
  "first_threshold_rubric_score": 36.67,
  "first_threshold_min_rubric_score": 60.0,
  "first_threshold_margin": -23.33
}
```

字段含义：

- `first_threshold_blocked_candidate`
  - 第一个因为 rubric threshold 被 blocked 的非 baseline candidate。
- `first_threshold_blocker`
  - 原始 blocker 文本，保持和 decision JSON 一致。
- `first_threshold_rubric_score`
  - candidate 的 rubric 平均分。
- `first_threshold_min_rubric_score`
  - 本次 decision 使用的阈值。
- `first_threshold_margin`
  - `rubric_score - threshold`。
  - 负数表示没过线，正数表示超过门槛。

文本 summary 对应：

```text
decision_first_threshold_candidate=tiny-candidate
decision_first_threshold_score=36.67
decision_first_threshold_min=60.0
decision_first_threshold_margin=-23.33
```

## 运行流程

v323 不改变主流程，只是在读取 decision JSON 后增加诊断投影：

```text
benchmark_scorecard_decision.json
  -> candidate_evaluations
  -> nonbaseline blocked rows
  -> first blocker starting with rubric_avg_score below
  -> score / threshold / margin
  -> top-level summary JSON/text
```

如果没有 threshold blocker，字段保持 `None`，不会伪造诊断。

## 输入输出

输入：

- `scorecard-decision/benchmark_scorecard_decision.json`
- 其中的 `min_rubric_score`
- 其中的 `candidate_evaluations[*].blockers`

输出：

- `tiny_scorecard_comparison_smoke_summary.json`
- `tiny_scorecard_comparison_smoke_summary.txt`

这些输出是 evidence summary，不是新评分文件，也不是训练结果。

## 测试覆盖

聚焦测试：

```text
python -B -m unittest tests.test_tiny_scorecard_comparison_smoke -v
```

覆盖点：

- 直接构造 decision payload，断言 threshold candidate、blocker、score、threshold 和 margin。
- 真实 tiny smoke 使用 `--decision-min-rubric-score 60`，并在 blocked 时断言 candidate 是 `tiny-candidate`、threshold 是 `60.0`、margin 为负。
- 文本 summary 输出 threshold 字段。
- 没有 threshold blocker 时输出 `None`，避免误报。

## 运行证据

归档位置：

```text
d/323/图片
d/323/解释/说明.md
```

截图证明：

- 聚焦测试通过。
- 真实 smoke summary 展示 threshold diagnostics。
- summary JSON 中也保留机器可读字段。

## 一句话总结

v323 把 tiny decision threshold 从“可配置”推进到“可诊断”，让 blocked smoke 能直接说明候选分数、门槛和差距。
