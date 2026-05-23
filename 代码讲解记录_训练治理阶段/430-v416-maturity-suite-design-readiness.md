# v416 maturity suite-design readiness 代码讲解

## 本版目标与边界

v416 的目标是把 v415 registry 已聚合的 release-readiness suite-design delta 继续带到 maturity summary 和 maturity narrative。这样项目级成熟度报告不仅能看到 benchmark-history regression、requirement change 和 failed-reason drift，也能看到 suite-design not-ready 增量、suite-design regression、design-change delta 以及最大变化幅度。

本版不新增 benchmark history 统计口径，不改变 release readiness comparison 的 delta 计算，也不重新训练模型。它只做下游消费：registry 已经给出机器可读字段，maturity 层负责把这些字段变成项目级状态、推荐语、CLI 输出和人读报告。

## 前置链路

本版接在 v411-v415 的 suite-design 链路后面：

- v411：release bundle 携带 benchmark-history suite-design readiness。
- v412：release gate 消费该字段。
- v413：release readiness dashboard 展示该字段。
- v414：release readiness comparison 计算 suite-design/design-change delta。
- v415：registry 聚合这些 delta，并输出到 CSV、HTML、leaderboard 和 CLI。

v416 继续向 maturity 层推进，但仍保持“消费已有证据”的边界。

## 关键文件

### `src/minigpt/maturity.py`

`_release_readiness_context()` 新增读取 registry summary 中的字段：

- `benchmark_history_suite_design_non_comparison_ready_delta_count`
- `benchmark_history_suite_design_non_comparison_ready_regression_count`
- `benchmark_history_design_comparison_changed_delta_count`
- `max_abs_benchmark_history_suite_design_non_comparison_ready_entries_delta`
- `max_abs_benchmark_history_design_comparison_changed_entries_delta`

`_summary()` 将这些字段转换成 maturity summary 的人读命名：

- `release_readiness_benchmark_suite_design_delta_count`
- `release_readiness_benchmark_suite_design_regression_count`
- `release_readiness_benchmark_design_change_delta_count`
- `release_readiness_max_benchmark_suite_design_delta`
- `release_readiness_max_benchmark_design_change_delta`

`_release_readiness_trend_status()` 在 suite-design regression 大于 0 时返回 `benchmark-regressed`。这意味着即使普通 benchmark-history regression count 为 0，只要 suite-design not-ready 是正向恶化，成熟度趋势也会进入 review。

### `src/minigpt/maturity_narrative_summary.py`

`build_maturity_narrative_summary()` 把 maturity summary/context 中的 suite-design 字段继续放进 narrative summary。

`_release_summary()` 负责兼容两种来源：

- 新的 `release_readiness_context` 字段。
- 已落入 maturity summary 的 `release_readiness_*` 字段。

如果 `suite_design_regression_count > 0`，它会把 release trend 归一为 `benchmark-regressed`，并让 portfolio status 进入 `review`。

### `src/minigpt/maturity_narrative_sections.py`

Release Quality Trend 的 claim 增加：

- `benchmark suite-design deltas`
- `suite-design regressions`
- `design changes`
- `max suite-design delta`
- `max design-change delta`

这让 HTML/Markdown narrative 不只给出状态，还能解释状态为什么从 stable/improved 变成 benchmark-regressed。

### `src/minigpt/maturity_artifacts.py`

Maturity summary 的 Markdown、HTML stat cards 和 Release Readiness Trend Context 表格都新增 suite-design 字段。它们是人读证据，不改变 JSON 的原始统计含义。

### `src/minigpt/maturity_narrative_artifacts.py`

Narrative 的 Portfolio Summary 和 HTML stat cards 新增 release benchmark suite/design 字段，保证成熟度叙事入口能看到同样的 suite-design regression context。

### `scripts/build_maturity_summary.py` 与 `scripts/build_maturity_narrative.py`

两个 CLI 都打印新增字段，方便 CI 或人工运行时直接从 stdout 确认：

```text
release_readiness_benchmark_suite_design_delta_count
release_readiness_benchmark_suite_design_regression_count
release_readiness_benchmark_design_change_delta_count
release_readiness_max_benchmark_suite_design_delta
release_readiness_max_benchmark_design_change_delta
```

## 测试覆盖

`tests/test_maturity.py` 增加 suite-design regression 用例：构造 registry delta summary，只让 suite-design regression 为正，断言 maturity trend 变为 `benchmark-regressed`、overall status 变为 `warn`，并出现明确的 suite-design review 推荐。

`tests/test_maturity_narrative.py` 增加 release suite-design regression 用例：断言 narrative summary、Release Quality Trend claim 和 portfolio status 都消费新增字段。

`tests/test_maturity_artifacts.py` 验证 Markdown/HTML 渲染中出现 suite-design regression 字段，防止 JSON 有字段但报告不可见。

本轮验证：

- 定向成熟度测试：`36 passed`
- 全量测试：`707 passed`
- source encoding hygiene：`status=pass`
- 语法编译与 diff 检查：通过

## 运行证据

`d/416` 归档了本版截图和说明：

- `d/416/图片/01-maturity-suite-design-readiness-evidence.png`
- `d/416/解释/v416-maturity-suite-design-readiness-evidence.html`
- `d/416/解释/说明.md`

截图中的核心证据是 maturity summary 顶部卡片与 Release Readiness Trend Context 表格同时展示 suite-design delta/regression/design-change 字段，并把 release trend 标为 `benchmark-regressed`。

一句话总结：v416 把 suite-design readiness regression 从 registry 多 run 汇总推进到 maturity 项目级评审层。
