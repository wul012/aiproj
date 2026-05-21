# 第一百三十八篇代码讲解：第344版 benchmark history maturity narrative

本版目标，是让 v343 新增的 benchmark history ledger 进入 maturity narrative 主线。

v343 已经能把 scorecard comparison 和 scorecard decision 串成历史账本；v344 不再新增一个孤立报告，而是把这份账本变成成熟度叙事的一部分。这样项目后续复盘时，不只看到“当前 decision 是什么”，还可以看到“这类 benchmark 结果在历史上是否稳定、是否 ready、是否有 regression”。

本版不做新的训练，不新增 benchmark case，也不改模型结构。它只消费已有 `benchmark_history.json`，并把其中的 readiness、boundary 和 regression 信号接入 maturity narrative。

## 本版所处链路

前置版本链路是：

```text
v317-v318: tiny scorecard comparison / decision smoke
v326-v330: decision taxonomy 与 remediation 证据
v343: benchmark history ledger
v344: maturity narrative consumes benchmark history
```

所以 v344 的核心角色是“把历史证据接入组合叙事”，而不是继续做新的 comparison 计算。

## 输入证据

新增可选输入：

```text
benchmark_history.json
```

CLI 参数是：

```text
--benchmark-history <path>
```

如果没有传入，`build_maturity_narrative()` 会在项目内自动发现：

```text
runs/**/benchmark-history/benchmark_history.json
runs/**/benchmark_history.json
```

这保持了向后兼容：旧项目没有 benchmark history 时不会直接变成 incomplete，只会在 recommendations 里提示后续应该补 history ledger。

## summary 新字段

`maturity_narrative_summary.py` 新增 history 汇总字段：

```text
benchmark_history_count
benchmark_history_entry_count
benchmark_history_ready_count
benchmark_history_promote_count
benchmark_history_review_count
benchmark_history_blocked_count
benchmark_history_case_regression_entry_count
benchmark_history_generation_flag_regression_entry_count
benchmark_history_model_quality_claim_counts
benchmark_history_boundary_counts
benchmark_history_best_candidate
benchmark_history_latest_boundary
```

这些字段的语义是：

- `*_count` 说明 history ledger 数量和 entry 状态分布。
- `best_candidate` 说明当前 history 里最后一个可引用的最佳候选。
- `latest_boundary` 说明最新 entry 属于 real benchmark candidate、mixed readiness，还是 tiny-smoke plumbing。
- regression count 说明这条历史链里是否有 case 或 generation-quality 反向证据。

## portfolio status 规则

本版把 history 当成真实治理信号：

```text
blocked_count > 0 -> portfolio review
review_count > 0 -> portfolio review
case_regression_entry_count > 0 -> portfolio review
generation_quality_flag_regression_entry_count > 0 -> portfolio review
```

这意味着 maturity narrative 不只是展示 history，而会把 history 中的不稳定性反映到最终 `portfolio_status`。

## sections 与 renderer

`maturity_narrative_sections.py` 新增 section：

```text
Benchmark History
```

这个 section 说明：

- history ledger 覆盖了多少 entry
- ready/review/blocked 分布如何
- best candidate 是谁
- latest boundary 是什么

`maturity_narrative_artifacts.py` 的 Markdown 和 HTML summary 也增加了 history 统计字段，让 reviewer 不必打开 JSON 才能看到 history 状态。

## CLI 输出

`scripts/build_maturity_narrative.py` 新增：

```text
--benchmark-history
```

并在 stdout 输出：

```text
benchmark_histories
benchmark_history_entries
benchmark_history_ready
benchmark_history_boundary
```

这让脚本输出可以被 CI 或人工 smoke 直接读取。

## 测试覆盖

`tests/test_maturity_narrative.py` 新增/增强覆盖：

- ready portfolio 可以消费 benchmark history
- evidence matrix 包含 `benchmark history ledger`
- Markdown/HTML 输出包含 history summary 和 section
- generation-quality flag regression 的 history 会把 portfolio 推到 review

这些测试保护的不是单纯字段存在，而是 history 真的参与了成熟度判断。

## 边界说明

v344 仍然不把 tiny smoke 当成模型质量证明。history 中的 `boundary` 会被保留和展示，tiny-smoke 仍然只是 plumbing evidence。

本版也不代替标准 benchmark。它只是让已有 benchmark 证据具备跨版本叙事能力。

## 一句话总结

v344 把 benchmark history 从独立账本提升为 maturity narrative 的治理输入，让历史评测证据可以影响项目组合状态和后续建议。
