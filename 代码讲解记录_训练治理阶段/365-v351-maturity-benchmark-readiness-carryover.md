# 第一百四十五篇代码讲解：第351版 maturity benchmark readiness carryover

本版目标，是把 v350 已经进入 registry 的 benchmark-history readiness regression 继续带进 maturity summary 和 maturity narrative。

v350 解决的是“多 run registry 能看见 benchmark-regressed”；v351 解决的是“项目级成熟度结论也能看见 benchmark-regressed”。如果 registry 已经知道某个 release readiness comparison 出现 benchmark-history status 退化、case regression 增加、generation flag regression 增加或 boundary 改变，maturity summary 和 maturity narrative 就不应该仍然只关注 CI/coverage/release status。

本版不做三件事：

- 不新增新的独立报告层。
- 不把 benchmark-history regression 解释为模型能力下降。
- 不改变 benchmark history、release readiness comparison 或 registry 的原始判定算法。

它只做证据链的向上承接：registry 已经生成的趋势字段，进入 maturity summary，再进入 narrative。

## 前置路线

这版接在 v343-v350 的 benchmark history 链条之后：

- v343 生成 benchmark history ledger。
- v344 让 maturity narrative 消费 benchmark history。
- v345-v347 让 audit、bundle、gate 消费 benchmark history。
- v348 让 release readiness 显示 benchmark history。
- v349 让 release readiness comparison 对比 benchmark history。
- v350 让 registry 汇总 `benchmark-regressed`。

v351 的位置在更上层：maturity summary 和 maturity narrative 是项目展示入口。如果这里不接 benchmark-history regression，那么 reviewer 仍要回到 registry 才能知道项目级趋势为什么需要 review。

## 关键修改文件

### `src/minigpt/maturity.py`

这是 maturity summary 的核心计算入口。

本版新增的核心字段来自 registry 的 `release_readiness_delta_summary`：

```text
benchmark_history_regression_count
benchmark_history_status_changed_count
benchmark_history_boundary_changed_count
max_abs_benchmark_history_case_regression_delta
max_abs_benchmark_history_generation_flag_regression_delta
```

这些字段会被写入 summary：

```text
release_readiness_benchmark_history_regression_count
release_readiness_benchmark_history_status_changed_count
release_readiness_benchmark_history_boundary_changed_count
release_readiness_max_benchmark_history_case_regression_delta
release_readiness_max_benchmark_history_generation_flag_regression_delta
```

`_release_readiness_trend_status()` 现在会在 coverage regression 之后识别 `benchmark-regressed`。这个顺序是保守的：

- coverage regression 仍是基础测试门禁问题，优先级最高。
- benchmark-history regression 是模型评估证据边界问题，独立于普通 readiness regressed。
- CI regression 继续保留自己的分类。

`_summary()` 也把 `benchmark-regressed` 视为 maturity review 信号。也就是说，只要 release readiness trend 是 benchmark-regressed，即使 capability matrix 本身全 pass，项目成熟度也会从 pass 降到 warn。

### `src/minigpt/maturity_artifacts.py`

这个文件负责 maturity summary 的 Markdown/HTML 渲染。

本版新增：

- Overview 表里的 `Release readiness benchmark-history regressions`。
- Release Readiness Trend Context 表里的 benchmark-history regression、status change、boundary change、case-regression delta、generation-flag regression delta。
- HTML 顶部 stat card 里的 `Benchmark regressions`。

这些是展示层字段，不重新计算趋势，只渲染 `maturity.py` 已经算好的结果。

### `scripts/build_maturity_summary.py`

CLI stdout 新增三项：

```text
release_readiness_benchmark_history_regression_count
release_readiness_benchmark_history_status_changed_count
release_readiness_benchmark_history_boundary_changed_count
```

这样在 CI 或命令行 smoke 中，不打开 JSON/HTML 也能判断 benchmark-history regression 是否进入 maturity summary。

### `src/minigpt/maturity_narrative_summary.py`

这个文件把 maturity summary、registry、request history、benchmark scorecard、benchmark history、dataset card 合成 narrative summary。

本版新增的关键点是 `_release_summary()` 会继续承接 maturity summary 里的 benchmark-history regression 字段。这样即使 narrative 主要读取的是 maturity summary，也不会丢失 registry 的 benchmark-regressed 趋势。

`_portfolio_status()` 也把 `benchmark-regressed` 和 `benchmark_history_regression_count > 0` 视为 review 信号。

### `src/minigpt/maturity_narrative_sections.py`

Release Quality Trend 的 claim 现在会写出：

```text
benchmark-history regressions=<n>
max benchmark case-regression delta=<n>
benchmark boundary changes=<n>
```

这句话的边界很重要：它说的是 release evidence quality，而不是 generated text quality。benchmark-history readiness regression 只能说明证据链变差或边界改变，不能自动证明模型能力下降。

### `src/minigpt/maturity_narrative_artifacts.py`

Markdown 和 HTML 输出新增 benchmark-history regression 字段：

- `Release benchmark-history regressions`
- `Release benchmark-history boundary changes`
- HTML stat card `Benchmark regressions`
- HTML stat card `Benchmark boundary changes`

### `scripts/build_maturity_narrative.py`

CLI stdout 新增：

```text
release_readiness_benchmark_history_regression_count
release_readiness_benchmark_history_boundary_changed_count
```

这让 narrative smoke 可以直接证明 `benchmark-regressed` 已经进入 portfolio review。

## 输入输出链路

输入从 registry 开始：

```text
runs/registry/registry.json
  -> release_readiness_delta_summary.benchmark_history_regression_count
  -> maturity_summary.summary.release_readiness_benchmark_history_regression_count
  -> maturity_narrative.summary.release_readiness_benchmark_history_regression_count
  -> Release Quality Trend section
  -> portfolio_status=review
```

输出包括：

- `maturity_summary.json`
- `maturity_summary.md`
- `maturity_summary.html`
- `maturity_narrative.json`
- `maturity_narrative.md`
- `maturity_narrative.html`
- CLI stdout key/value diagnostics

这些输出都是项目级证据，不是训练产物，也不是模型质量证明。

## 测试覆盖

新增/加强的测试集中在两处：

- `tests/test_maturity.py`
- `tests/test_maturity_narrative.py`

关键断言包括：

- registry 中 `benchmark_history_regression_count=1` 时，maturity summary 的 `release_readiness_trend_status` 是 `benchmark-regressed`。
- maturity summary 的 `overall_status` 会进入 `warn`。
- benchmark-history status change、boundary change、case-regression delta、generation-flag regression delta 都会进入 summary 和 context。
- recommendation 会提示 review benchmark-history readiness regression。
- maturity narrative 会把 portfolio_status 设为 `review`。
- Release Quality Trend section 会写出 benchmark-history regression、case-regression delta 和 boundary changes。
- Markdown/HTML 输出能看到 benchmark-history regression 字段。

这组测试保护的是证据承接：v350 的 registry 信号不能在 maturity 层被吞掉。

## 运行证据

本版 smoke 构造了一个最小项目：

- registry 中有 `release_readiness_comparison_counts={"benchmark-regressed": 1, "stable": 1}`。
- registry delta summary 中 benchmark-history regression count 为 1。
- CI 和 coverage regression count 都是 0。
- request history、scorecard、decision、benchmark history、dataset card 都是最小可读证据。

命令输出确认：

```text
release_readiness_trend_status=benchmark-regressed
release_readiness_benchmark_history_regression_count=1
release_readiness_benchmark_history_boundary_changed_count=1
portfolio_status=review
```

Playwright 截图保存在：

```text
d/351/图片/01-maturity-summary-benchmark-regression-html.png
d/351/图片/02-maturity-narrative-benchmark-regression-html.png
d/351/图片/03-verification-summary.png
```

说明文档在：

```text
d/351/解释/说明.md
```

## 边界说明

v351 仍然不声称模型质量下降。

`benchmark-regressed` 的含义是：release readiness comparison 看到 benchmark-history readiness 证据边界变差，例如 status 变差、ready 变少、review/blocker/regression 增多或 latest boundary 变化。它是项目治理证据，不是模型能力结论。

## 一句话总结

v351 把 registry 层的 benchmark-history readiness regression 推进到 maturity summary 和 maturity narrative，让项目级 review 能直接看到这条评估证据边界的退化。
