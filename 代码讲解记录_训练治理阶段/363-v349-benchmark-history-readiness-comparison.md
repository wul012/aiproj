# 第一百四十三篇代码讲解：第349版 benchmark history readiness comparison

本版目标，是让 v348 已经进入 release readiness dashboard 的 benchmark history 边界继续进入 release readiness comparison。

v343 生成 benchmark history ledger；v344 到 v348 依次把它带进 maturity narrative、project audit、release bundle、release gate 和 release readiness。v349 负责补最后一个对比视角：当 baseline readiness 和 candidate readiness 放在一起时，报告不能只说 panel changed，而要说清楚 benchmark history status、ready 数、regression 数、quality claim 和 latest boundary 是如何变化的。

本版不训练模型，不新增 benchmark，也不改变 release readiness 的生成逻辑。它只消费已有 `release_readiness.json` summary 字段，生成对比证据。

## 本版所处链路

前置链路是：

```text
benchmark history -> release gate / release bundle -> release readiness
```

v349 追加的是：

```text
release readiness -> release readiness comparison
```

它的角色是 trend review：单个 readiness 报告负责说明当前版本为什么 review；comparison 报告负责说明当前版本相比 baseline 是改善、退化，还是只是 panel 边界变化。

## 输入输出

输入仍然是一个或多个 readiness dashboard：

```text
release_readiness.json
```

命令行仍然使用：

```powershell
python scripts\compare_release_readiness.py --readiness <baseline>\release_readiness.json --readiness <current>\release_readiness.json
```

输出仍然是：

```text
release_readiness_comparison.json
release_readiness_comparison.csv
release_readiness_deltas.csv
release_readiness_comparison.md
release_readiness_comparison.html
```

新增的是 rows、deltas、summary、CSV、Markdown、HTML 和 CLI stdout 中的 benchmark history 对比字段。

## 关键文件

`src/minigpt/release_readiness_comparison.py`

- `_row_from_report()` 从 readiness summary 读取 `benchmark_history_status`、`entries`、`ready/review/blocked`、case regression、generation-flag regression、model quality claim 和 latest boundary。
- `_delta_from_baseline()` 计算 benchmark history status delta、ready/review/blocked delta、regression delta、quality claim changed 和 boundary changed。
- `_has_benchmark_history_delta()` 判断本次对比是否存在 benchmark history 变化。
- `_is_benchmark_history_regression()` 判断这种变化是否是退化：status 变差、ready 变少、review/blocked/regression 变多都会被视为回归。
- `_recommendations()` 在 benchmark history regression 出现时给出专门建议，不把它混进 CI workflow 或 test coverage regression。

`src/minigpt/release_readiness_comparison_artifacts.py`

- comparison CSV 增加 benchmark history 行级字段。
- delta CSV 增加 benchmark history delta 字段。
- Markdown summary 增加 `Benchmark history deltas` 和 `Benchmark history regressions`。
- Markdown/HTML matrix 增加 benchmark history status、ready、regressions 和 boundary。
- Markdown/HTML delta 表增加 benchmark status delta、case regression delta 和 boundary changed。

`scripts/compare_release_readiness.py`

- stdout 增加：

```text
benchmark_history_deltas
benchmark_history_regressions
```

这让 shell-only smoke 和 CI 日志可以直接看出 benchmark history 是否跨版本退化。

`tests/test_release_readiness_comparison.py`

- fixture 增加 benchmark history summary 和 panel。
- 新增退化测试：baseline 为 `pass/ready=1/regressions=0`，candidate 为 `warn/ready=0/case_regressions=2/generation_flag_regressions=1`。
- 新增改善测试：baseline warning，candidate pass，确保 regression count 不误报。
- 输出测试确认 CSV 和 delta CSV 都包含 benchmark history 字段。

## 核心数据结构

row 级字段表示每个 readiness 报告的当前状态：

```text
benchmark_history_status
benchmark_history_ready
benchmark_history_review
benchmark_history_blocked
benchmark_history_case_regressions
benchmark_history_generation_flag_regressions
benchmark_history_model_quality_claim
benchmark_history_latest_boundary
```

delta 级字段表示相对 baseline 的变化：

```text
benchmark_history_status_delta
benchmark_history_ready_delta
benchmark_history_case_regression_delta
benchmark_history_generation_flag_regression_delta
benchmark_history_model_quality_claim_changed
benchmark_history_latest_boundary_changed
```

status 使用轻量顺序：

```text
missing/fail/blocked < warn/review < pass/ready
```

这不是模型分数，只是 release review 状态排序。

## 测试覆盖

聚焦测试验证三件事：

- benchmark history 从 pass 退到 warn 时，summary 出现 `benchmark_history_regression_count=1`。
- benchmark history 从 warn 改善到 pass 时，delta 仍被记录，但不算 regression。
- CSV、delta CSV、Markdown 和 HTML 都能暴露新增字段。

这些测试保护的是对比归因：benchmark history regression 应该独立显示，不应该被误归类成 CI workflow 或 coverage regression。

## 运行证据

本版证据归档在：

```text
d/349
```

其中包含 release readiness comparison HTML 截图和验证摘要图。HTML 截图里可以看到：

```text
Benchmark deltas = 1
Benchmark regressions = 1
CI regressions = 0
Coverage regressions = 0
```

## 边界说明

v349 仍然不把 benchmark history 当成模型质量证明。它只比较 evidence status 和 boundary。

如果 candidate 的 latest boundary 是 `tiny-smoke-plumbing-evidence`，comparison 会把它作为 review/退化线索展示出来，而不是说模型能力下降或提升。

## 一句话总结

v349 把 benchmark history 从单次 readiness 展示推进到跨版本 readiness 对比，让发布评审能看清 benchmark 证据边界是改善还是退化。
