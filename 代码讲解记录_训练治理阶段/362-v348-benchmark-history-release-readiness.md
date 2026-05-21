# 第一百四十二篇代码讲解：第348版 benchmark history release readiness

本版目标，是让 v347 release gate 已经识别出的 benchmark history 边界继续进入 release readiness dashboard。

v343 生成 benchmark history ledger；v344 让 maturity narrative 使用它；v345 让 project audit 审计它；v346 把它带入 release bundle；v347 让 release gate 检查它。v348 负责把最终发布看板补齐：readiness 不应该只显示一个笼统的 `Gate warn`，还要单独显示 benchmark history status、entries、ready/review/blocked、regression、quality claim 和 latest boundary。

本版不训练模型，不新增 benchmark，也不改变 release gate 的判断。它只把已有 gate/bundle 证据整理到最终 readiness review surface。

## 本版所处链路

前置链路是：

```text
benchmark history -> maturity narrative -> project audit -> release bundle -> release gate
```

v348 追加的是：

```text
release gate / release bundle -> release readiness
```

它的角色是 final review visibility：最终 readiness dashboard 要能解释为什么 release 进入 review，而不是只留下一个无法定位来源的 warn。

## 输入输出

输入仍然是 release readiness 既有输入：

```text
release_bundle.json
gate_report.json
project_audit.json
request_history_summary.json
maturity_summary.json
ci_workflow_hygiene.json
test_coverage_report.json
```

本版不新增命令行输入路径。benchmark history 来源优先级是：

```text
gate check -> gate summary -> bundle summary
```

输出仍然是：

```text
release_readiness.json
release_readiness.md
release_readiness.html
```

新增的是 summary、panel、CLI stdout、Markdown 和 HTML stats 中的 benchmark history 字段。

## 关键文件

`src/minigpt/release_readiness.py`

- panels 新增 `Benchmark History`。
- `_benchmark_history_panel()` 从 gate check、gate summary、bundle summary 提取 benchmark history 字段。
- `_benchmark_history_summary()` 把 status、entries、ready、review、blocked、regression、quality claim 和 boundary 写入 readiness summary。
- `_gate_check()` 从 gate report 的 checks 中找到 `benchmark_history_gate_check`。
- warning status 会让 readiness 进入 `review`，blocked/fail status 会进入失败链路。

`src/minigpt/release_readiness_artifacts.py`

- Markdown summary 增加 benchmark history status、entries、ready、regressions 和 boundary。
- HTML stats 增加 `Bench history` 和 `Bench boundary`。
- panel grid 自动显示新增 Benchmark History panel。

`scripts/build_release_readiness.py`

- stdout 增加：

```text
benchmark_history_status
benchmark_history_entries
benchmark_history_ready
benchmark_history_boundary
```

这些字段让命令行 smoke 能直接确认 readiness 是否承接了 gate/bundle 的 benchmark history 边界。

## 核心数据流

如果 gate report 中有 `benchmark_history_gate_check`，readiness panel detail 会保留：

```text
gate_check=warn
```

如果 gate summary 缺少 benchmark history 字段，但 bundle summary 仍有字段，readiness 会走 bundle fallback，并仍然显示：

```text
status=warn
ready=0
boundary=tiny-smoke-plumbing-evidence
```

这样 v348 同时覆盖了新 gate 报告和过渡期 bundle-only 报告。

## 测试覆盖

`tests/test_release_readiness.py` 覆盖：

- ready release 中 benchmark history pass，summary 和 panel 都为 pass。
- benchmark history warning 会让 readiness 变为 `review`。
- warning case 保留 `case_regressions=1`、`gate_check=warn` 和 `tiny-smoke-plumbing-evidence`。
- gate summary/check 缺失时，readiness 能从 bundle summary fallback。
- 输出 Markdown/HTML 仍能正常渲染。

这些测试保护的是最终看板解释能力，不只是 JSON 字段存在。

## 运行证据

本版证据归档在：

```text
d/348
```

其中包含 release readiness 聚焦测试、readiness CLI smoke、全量验证和 Playwright/Chrome 打开的 release readiness HTML 截图。

## 边界说明

v348 仍然不把 benchmark history 解释成模型质量证明。它只是把证据状态和边界带到最终 readiness dashboard。

如果 latest boundary 是 `tiny-smoke-plumbing-evidence`，或 quality claim 是 `not_claimed`，readiness 会把它保留为 review 线索，而不是包装成可发布的模型能力证明。

## 一句话总结

v348 把 benchmark history 从 release gate 和 release bundle 带入 release readiness，让最终发布看板能解释 benchmark 证据为什么需要 review。
