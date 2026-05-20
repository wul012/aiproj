# v319 tiny decision diagnostics smoke

## 本版目标和边界

v318 已经把 tiny benchmark smoke 接到了 scorecard decision：

```text
baseline tiny smoke -> candidate tiny smoke -> scorecard comparison -> scorecard decision
```

v319 不改变 decision 算法，也不扩大模型训练规模。本版解决的是证据可读性问题：当 tiny candidate 被 `blocked` 或进入 `review` 时，CI 控制台和顶层 summary 应该直接说明“哪个候选被挡住、第一条 blocker/review item 是什么、系统推荐下一步做什么”，而不是要求读者再打开 `benchmark_scorecard_decision.json`。

这版仍然不宣称 tiny 模型质量。`model_quality_claim` 继续是 `not_claimed`，`decision_status=blocked` 依然是合理的 smoke 结果。

## 前置能力

本版基于：

- v315 的 CPU tiny train -> standard-suite eval -> generation-quality -> benchmark scorecard smoke。
- v316 的 same-checkpoint pair baseline 证据。
- v317 的双 tiny scorecard comparison。
- v318 的 scorecard decision 产物接入。

v319 的新增点只发生在顶层 smoke 摘要层：把 decision JSON 中已经存在的 candidate evaluation、blocker、review item 和 recommendation 摘出来，写入 `tiny_scorecard_comparison_smoke_summary.json` 与 `.txt`。

## 关键文件

- `scripts/run_tiny_scorecard_comparison_smoke.py`
  - `decision_summary()` 读取 `candidate_evaluations`，排除 baseline 后识别 blocked 与 review candidate。
  - 新增 `blocked_candidate_names`、`review_candidate_names`、`first_blocked_candidate`、`first_blocker`、`first_review_candidate`、`first_review_item` 和 `first_recommendation`。
  - `render_summary()` 把 `decision_blocked_candidates`、`decision_first_blocker`、`decision_review_candidates`、`decision_first_review_item` 和 `decision_first_recommendation` 写进 line-oriented 文本摘要。

- `tests/test_tiny_scorecard_comparison_smoke.py`
  - 覆盖 summary render 中新增的 decision diagnostics。
  - 真实 smoke 链路中断言 blocked candidate names、review candidate names 和 first recommendation 进入 summary。

- `README.md`
  - 当前版本升级到 v319。
  - 说明本版是 decision diagnostics 的顶层可读性增强。

- `d/319`
  - 保存 v319 的命令输出截图和解释。

## 核心数据结构

`scorecard_decision` 摘要现在包含：

```json
{
  "decision_status": "blocked",
  "recommended_action": "keep_baseline_or_fix_candidate",
  "selected_name": null,
  "candidate_evaluation_count": 2,
  "blocked_candidate_count": 1,
  "blocked_candidate_names": ["tiny-candidate"],
  "review_candidate_names": [],
  "first_blocked_candidate": "tiny-candidate",
  "first_blocker": "rubric_avg_score below 80.0",
  "first_review_candidate": null,
  "first_review_item": null,
  "recommendation_count": 2,
  "first_recommendation": "Keep the baseline or fix candidate scorecard regressions before promotion."
}
```

字段语义：

- `blocked_candidate_names`
  - 非 baseline candidate 中带有 blockers 的候选名称。
- `review_candidate_names`
  - 非 baseline candidate 中有 review items 且没有 blockers 的候选名称。
- `first_blocker`
  - 第一条阻断原因，方便 CI 文本摘要直接显示失败原因。
- `first_review_item`
  - 第一条需要人工复核的原因。
- `first_recommendation`
  - decision 模块的首条后续建议。

## 运行流程

v319 沿用 v318 的四段命令链：

```text
baseline_smoke
candidate_smoke
scorecard_comparison
scorecard_decision
```

区别在最后的汇总阶段：

```text
benchmark_scorecard_decision.json
  -> decision_summary()
  -> tiny_scorecard_comparison_smoke_summary.json
  -> tiny_scorecard_comparison_smoke_summary.txt
  -> stdout
```

文本摘要会出现类似输出：

```text
decision_status=blocked
decision_blocked_candidates=tiny-candidate
decision_first_blocker=rubric_avg_score below 80.0
decision_first_recommendation=Keep the baseline or fix candidate scorecard regressions before promotion.
model_quality_claim=not_claimed
```

这让 CI 日志里的阻断原因足够明确，同时完整 JSON/CSV/Markdown/HTML decision artifact 仍然保留在 `scorecard-decision/` 目录中。

## 输入输出

典型命令：

```text
python -B scripts/run_tiny_scorecard_comparison_smoke.py --out-dir runs/v319-tiny-decision-diagnostics-smoke --suite-name standard-zh --case-token-cap 5 --max-iters 1 --eval-iters 1 --batch-size 2 --block-size 8 --n-embd 8 --force
```

顶层输出：

```text
runs/v319-tiny-decision-diagnostics-smoke/tiny_scorecard_comparison_smoke_summary.json
runs/v319-tiny-decision-diagnostics-smoke/tiny_scorecard_comparison_smoke_summary.txt
```

下游仍可消费完整 decision 产物：

```text
runs/v319-tiny-decision-diagnostics-smoke/scorecard-decision/benchmark_scorecard_decision.json
runs/v319-tiny-decision-diagnostics-smoke/scorecard-decision/benchmark_scorecard_decision.csv
runs/v319-tiny-decision-diagnostics-smoke/scorecard-decision/benchmark_scorecard_decision.md
runs/v319-tiny-decision-diagnostics-smoke/scorecard-decision/benchmark_scorecard_decision.html
```

这些产物是本版的运行证据，不是模型能力证明。

## 测试覆盖

- `tests.test_tiny_scorecard_comparison_smoke`
  - 覆盖 summary render 的新增文本字段。
  - 跑真实 tiny baseline/candidate、scorecard comparison 和 decision。
  - 当 decision 是 `blocked` 时断言 blocked candidate 与 first blocker 不为空。
- focused tests
  - 覆盖 tiny comparison smoke、standard benchmark smoke、scorecard comparison 和 scorecard decision。
- full unittest
  - 确认全仓测试仍通过。
- source encoding、py_compile、diff check
  - 确认新增摘要字段没有引入编码、语法和空白问题。

测试保护的是“decision 诊断能进入顶层 smoke 证据”，不是固定某次 tiny candidate 必须变好。

## 运行证据

归档位置：

```text
d/319/图片
d/319/解释/说明.md
```

截图覆盖：

- 单测与 focused tests。
- 真实 smoke summary。
- decision JSON diagnostics 字段。
- decision/comparison 产物存在性。
- source encoding、full unittest、py_compile、diff check 和静态扫描。

## 一句话总结

v319 把 tiny scorecard decision 的阻断和复核原因提升到顶层 smoke 摘要，让 CI 日志直接可读，同时继续保持“这是训练治理证据，不是模型质量宣称”的边界。
