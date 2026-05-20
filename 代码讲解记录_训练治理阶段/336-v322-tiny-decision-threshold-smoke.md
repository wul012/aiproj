# v322 tiny decision threshold smoke

## 本版目标和边界

v321 做的是 artifact 层结构收口。v322 回到 tiny scorecard comparison smoke 的真实运行链路，解决一个小但关键的问题：promotion decision 的 rubric 门槛原来硬编码为 `80`。

这版的目标是把门槛变成显式配置：

- 命令行可传 `--decision-min-rubric-score`。
- 真实 decision 命令收到对应的 `--min-rubric-score`。
- summary JSON 和文本摘要都记录这个阈值。
- 非法阈值提前拒绝。

边界同样明确：v322 不改 `benchmark_scorecard_decision.py` 的决策算法，不改 rubric 评分，不声称 tiny 模型能力提升。它改的是 smoke orchestration 的可复现配置。

## 前置能力

本版基于 v317-v320 的 tiny scorecard comparison 主线：

- v317：两次真实 tiny benchmark smoke 之后做 scorecard comparison。
- v318：comparison 后继续生成 scorecard decision。
- v319：把 blocked/review diagnostics 提到顶层 summary。
- v320：baseline/candidate 可以使用不同训练预算。

v322 是这条路线的自然补全：既然预算已经能显式配置，promotion decision 的 rubric gate 也应该显式记录，避免 CI 结果只知道 blocked，却不知道当时用的门槛是多少。

## 关键文件

- `scripts/run_tiny_scorecard_comparison_smoke.py`
  - 新增 `--decision-min-rubric-score`，默认 `80.0`。
  - `build_run_config()` 保存 `decision_min_rubric_score`。
  - decision 子命令从 `run_config` 读取阈值并传给 `build_benchmark_scorecard_decision.py --min-rubric-score`。
  - `render_summary()` 输出 `config_decision_min_rubric_score`。
  - `build_run_config()` 拒绝小于 `0` 或大于 `100` 的阈值。

- `tests/test_tiny_scorecard_comparison_smoke.py`
  - 覆盖 summary 中的阈值字段。
  - 覆盖真实 smoke 传入 `--decision-min-rubric-score 60` 后，decision 命令包含 `--min-rubric-score 60.0`。
  - 覆盖默认阈值仍是 `80.0`。
  - 覆盖非法阈值会抛出 `ValueError`。

- `README.md`
  - 当前版本更新为 v322。
  - benchmark/model comparison 能力中加入 configurable decision rubric thresholds。
  - 记录 v322 checkpoint。

- `d/322`
  - 保存本版真实 smoke、decision 输出、JSON 配置和聚焦测试的截图说明。

## 核心数据结构

`run_config` 是 v322 的核心证据载体。新增字段：

```json
{
  "decision_min_rubric_score": 60.0
}
```

它和已有字段放在一起：

- `suite_name`
- `case_token_cap`
- `baseline_max_iters`
- `candidate_max_iters`
- `budget_mode`
- `baseline_seed`
- `candidate_seed`

这个设计的含义是：decision threshold 属于本次 smoke 的实验配置，而不是某个隐藏在脚本里的固定事实。

文本摘要中对应输出：

```text
config_decision_min_rubric_score=60.0
```

这样 CI 日志只看顶层 summary，也能知道本次 blocked/review/promote 是按什么 rubric 门槛判定的。

## 运行流程

v322 的运行链路是：

```text
parse args
  -> build_run_config()
     -> validate decision_min_rubric_score in 0..100
  -> baseline tiny smoke
  -> candidate tiny smoke
  -> compare_benchmark_scorecards.py
  -> build_benchmark_scorecard_decision.py --min-rubric-score <configured>
  -> build_summary()
  -> summary JSON/text
```

真实 v322 smoke 使用：

```text
--baseline-max-iters 1
--candidate-max-iters 2
--decision-min-rubric-score 60
```

输出中 candidate 仍然被 blocked：

```text
decision_first_blocker=rubric_avg_score below 60.0
```

这说明阈值确实进入了 decision 层。这里的 `status=pass` 只表示链路完成和证据完整，不表示 tiny candidate 应该被推广。

## 输入输出

输入：

- baseline/candidate tiny smoke 配置。
- suite 和 token cap。
- baseline/candidate 训练预算。
- `decision_min_rubric_score`。

输出：

- `tiny_scorecard_comparison_smoke_summary.json`
  - 机器可读 summary，包含 `run_config.decision_min_rubric_score`。
- `tiny_scorecard_comparison_smoke_summary.txt`
  - CI 友好的 key/value 文本，包含 `config_decision_min_rubric_score`。
- `scorecard-decision/benchmark_scorecard_decision.*`
  - 由 configured threshold 生成的 decision artifacts。

这些输出是只读证据，不是新的训练结果，也不是模型质量证书。

## 测试覆盖

聚焦测试：

```text
python -B -m unittest tests.test_tiny_scorecard_comparison_smoke -v
```

覆盖点：

- `render_summary()` 输出 `config_decision_min_rubric_score`。
- 真实 smoke 链路使用非默认阈值 `60`。
- summary JSON 记录 `decision_min_rubric_score=60.0`。
- decision command text 记录 `--min-rubric-score 60.0`。
- 默认配置仍得到 `80.0`。
- 阈值 `101.0` 被拒绝。

全量测试与编码检查在本版提交前继续作为收口验证。

## 运行证据

归档位置：

```text
d/322/图片
d/322/解释/说明.md
```

关键截图证明：

- 聚焦测试通过。
- 真实 tiny smoke 通过。
- summary text 记录阈值。
- decision stdout 使用阈值产生 blocker。
- summary JSON 保留可复现配置。

## 一句话总结

v322 把 tiny scorecard comparison smoke 的 promotion threshold 从隐藏常量提升为可复现配置，让 CI 证据能说明“按什么门槛判定”，而不是只说明“判定结果是什么”。
