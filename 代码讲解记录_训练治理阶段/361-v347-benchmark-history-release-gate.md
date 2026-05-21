# 第一百四十一篇代码讲解：第347版 benchmark history release gate

本版目标，是让 v346 已经进入 release bundle 的 benchmark history 继续进入 release gate 和 release gate profile comparison。

v343 生成 benchmark history ledger，v344 让 maturity narrative 使用它，v345 让 project audit 审计它，v346 把它带入 release bundle。v347 补上最后一段发布门禁：如果 release bundle 里已经写明 benchmark history 缺失、review、blocked、case regression、generation-quality flag regression 或 `model_quality_claim=not_claimed`，release gate 必须把这些边界显式显示出来。

本版不训练模型，不新增 benchmark 题集，不改变 tiny smoke 的模型质量边界。它只让发布门禁消费已有证据，并保持 legacy profile 对旧 bundle 的兼容。

## 本版所处链路

前置链路是：

```text
scorecard comparison -> scorecard decision -> benchmark history
benchmark history -> maturity narrative -> project audit -> release bundle
```

v347 追加的是：

```text
release bundle -> release gate -> release gate profile comparison
```

它的角色是 gate visibility：release bundle 已经携带的 benchmark history 风险，不能在门禁阶段被忽略。

## 输入输出

release gate 输入仍然是：

```text
release_bundle.json
```

新增可选兼容开关：

```text
--allow-missing-benchmark-history
```

输出仍然是：

```text
gate_report.json
gate_report.md
gate_report.html
```

新增的是 summary、policy、checks、CLI stdout 和 profile comparison 里的 benchmark history requirement 字段。

## 关键文件

`src/minigpt/release_gate.py`

- policy profile 新增 `require_benchmark_history`。
- standard/review/strict 默认要求 benchmark history release evidence。
- legacy 保持不要求，用于检查旧 release bundle。
- `build_release_gate()` 新增 `require_benchmark_history` 覆盖参数。
- checks 新增 `benchmark_history_gate_check`。
- summary 透出 benchmark history status、entries、ready、review、blocked、regression、quality claim 和 latest boundary。

`src/minigpt/release_gate_benchmark.py`

- 新增小模块，集中处理 benchmark history gate 结果和 detail 文案。
- `benchmark_history_gate_result()` 判断 pass/warn/fail。
- `benchmark_history_gate_detail()` 输出门禁详情，包含 entries、ready、review、blocked、regression、quality claim 和 boundary。
- 这个拆分避免 `release_gate.py` 再次超过大文件阈值，也让门禁判断更容易单独审阅。

`src/minigpt/release_gate_artifacts.py`

- Markdown summary 增加 benchmark history 状态、entries、ready、regressions 和 boundary。
- HTML stats 增加 `Bench history` 和 `Bench entries`。

`scripts/check_release_gate.py`

- 新增 `--allow-missing-benchmark-history`。
- stdout 增加：

```text
benchmark_history_status
benchmark_history_entries
benchmark_history_ready
benchmark_history_boundary
require_benchmark_history
```

`src/minigpt/release_gate_comparison.py`

- profile comparison 调用 release gate 时传递 `require_benchmark_history`。
- profile rows 记录 `require_benchmark_history_gate_check`。
- delta 记录 benchmark-history requirement 的 baseline/compared 差异。
- delta explanation 会写出 Benchmark-history requirement changes。

`src/minigpt/release_gate_comparison_artifacts.py`

- CSV、delta CSV、Markdown、HTML 都新增 benchmark-history requirement 字段。
- 这样比较 standard/review/strict/legacy 时，可以看出 legacy 为什么放行旧包。

## 核心判断逻辑

`benchmark_history_gate_result()` 先看策略：

- 如果当前 profile 不要求 benchmark history，直接 pass。
- 如果 audit check 和 bundle summary 都没有 benchmark history 状态，fail。
- 如果任一状态是 fail 或 missing，fail。
- 如果 bundle summary 里 `benchmark_history_blocked > 0`，fail。
- 如果有 review、case regression、generation flag regression、没有 entries、没有 ready，或 `model_quality_claim=not_claimed`，warn。
- 其余情况 pass。

这里区分了 blocked 和 review：blocked 会使 release gate 失败；review/regression/not_claimed 进入 needs-review。这样不把弱证据包装成 release-ready，也不把需要人工判断的边界一刀切成失败。

## 测试覆盖

`tests/test_release_gate.py` 覆盖：

- ready bundle 默认通过，并显示 benchmark history policy/check/summary 字段。
- benchmark history 缺失时 standard gate fail。
- legacy profile 对缺失 benchmark history 放行。
- review/regression/not_claimed 会让 gate warn。
- blocked count 会让 gate fail。
- 显式 override 能关闭 benchmark history 要求。

`tests/test_release_gate_comparison.py` 覆盖：

- profile comparison 的 fixture 带 benchmark history。
- legacy profile 中 `require_benchmark_history_gate_check=False`。
- 缺失 benchmark history 时 standard blocked、legacy approved。
- delta explanation 说明 Benchmark-history requirement changes。
- 输出渲染仍包含 profile matrix、delta CSV 和 HTML。

这些测试保护的是发布门禁的可见性，不只是字段透传。

## 运行证据

本版证据归档在：

```text
d/347
```

其中包含 release gate/profile comparison 聚焦测试、release gate CLI smoke、profile comparison smoke、全量验证、结构扫描和 Playwright/Chrome 打开的 gate/profile HTML 截图。

## 边界说明

v347 不把 benchmark history 本身变成模型质量证明。它只负责让 release gate 看见这份证据的状态和边界。

如果 evidence 是 tiny smoke plumbing evidence，或 model quality claim 是 `not_claimed`，gate 会进入 warning review，而不是把它当成真实模型能力提升。release gate 的输出是发布治理证据，不是模型能力评测报告。

legacy profile 仍然存在，是为了旧 release bundle 的可读性和过渡检查，不建议作为新版本发布的默认 profile。

## 一句话总结

v347 把 benchmark history 从 release bundle 接入 release gate，让历史评估证据在发布门禁和 profile comparison 中可见、可解释、可阻断。
