# v411 release bundle benchmark history suite design

## 本版目标和边界

v411 的目标是把 v410 已经进入 project audit 的 benchmark-history suite-design readiness 继续接到 release bundle。这样最终随 tag 保存的发布证据，不会只看到 benchmark history status/readiness requirement，而丢掉 prompt suite design 是否 comparison-ready 的解释。

本版不新增治理链，不训练 checkpoint，不扩展 release gate，也不改变 benchmark scorecard 打分。它只把已有的 history 字段传到 release bundle 的 context、summary、Markdown/HTML 和 CLI stdout。

## 前置能力

本版承接：

- v408：benchmark history ledger 保存 suite-design not-ready 和 design-change 计数。
- v409：maturity narrative 消费这些字段。
- v410：project audit 消费这些字段，并在 audit check 中触发 warning。

v411 位于发布证据打包层，负责把这些字段留在 release bundle 中，供后续 release gate/readiness 或人工审阅继续使用。

## 关键文件

### `src/minigpt/release_bundle_contexts.py`

`_benchmark_history_context()` 新增：

```text
suite_design_non_comparison_ready_entry_count
design_comparison_changed_entry_count
```

当传入新的 `benchmark_history.json` 时，字段优先来自 history summary；history 缺失时，继续使用 audit context 兜底。

`_status_from_benchmark_context()` 现在把 `suite_design_non_comparison_ready_entry_count > 0` 当成 warning 信号。这样 stale audit 仍是 pass 时，只要新的 benchmark history 暴露 suite-design not-ready，release bundle 也会进入 review-needed。

### `src/minigpt/release_bundle_support.py`

bundle summary 新增：

```text
benchmark_history_suite_design_non_comparison_ready_entries
benchmark_history_design_comparison_changed_entries
```

同时把 benchmark-history 的 entries、ready、review、blocked、regression、model-quality claim 和 boundary 改成优先使用当前 benchmark history context，再用 audit summary 兜底。这修掉了一个真实边界：旧 audit summary 可能仍写着 `ready=1`，但新的 benchmark history 已经因为 suite-design not-ready 变成 `ready=0`。

### `src/minigpt/release_bundle_artifacts.py`

Markdown Summary 新增：

```text
Benchmark history suite-design not-ready
Benchmark history design changes
```

HTML stats 新增：

```text
Bench design review
Bench design changes
```

这些字段是发布证据解释，不是新的模型能力证明。

### `scripts/build_release_bundle.py`

CLI stdout 新增：

```text
benchmark_history_suite_design_non_comparison_ready_entries
benchmark_history_design_comparison_changed_entries
```

这样自动化日志可以直接确认 bundle 是否保留了 suite-design history 边界。

### `tests/test_release_bundle.py`

测试覆盖新增和更新：

- ready release 默认 suite-design 计数为 `0`。
- 新 benchmark history suite-design not-ready 时，即使 audit summary 仍是 stale pass，bundle 也会变成 `review-needed`。
- suite-design not-ready 会让 `benchmark_history_status=warn`、`benchmark_history_ready=0`，并保留 failed reason 和 `suite-design-not-comparison-ready` boundary。
- Markdown/HTML 输出包含新增字段。
- `scripts/build_release_bundle.py` stdout 打印新增字段。

## 输入输出

输入仍是 release bundle 原有输入：

```text
registry.json
model_card.json
project_audit.json
request_history_summary.json
benchmark_history.json
ci_workflow_hygiene.json
test_coverage_report.json
```

输出新增字段：

```text
release_bundle.json
  summary.benchmark_history_suite_design_non_comparison_ready_entries
  summary.benchmark_history_design_comparison_changed_entries
  benchmark_history_context.suite_design_non_comparison_ready_entry_count
  benchmark_history_context.design_comparison_changed_entry_count

release_bundle.md/html
  Benchmark history suite-design not-ready
  Bench design review

CLI stdout
  benchmark_history_suite_design_non_comparison_ready_entries
  benchmark_history_design_comparison_changed_entries
```

## 测试覆盖

定向验证命令：

```text
python -m pytest tests\test_release_bundle.py -q
python -m py_compile src\minigpt\release_bundle_contexts.py src\minigpt\release_bundle_support.py src\minigpt\release_bundle_artifacts.py scripts\build_release_bundle.py tests\test_release_bundle.py
```

完整验证还包括全量 pytest、source encoding hygiene 和 `git diff --check`。

## 运行证据

运行截图与说明归档在：

```text
d/411/图片/01-release-bundle-history-suite-design-evidence.png
d/411/解释/说明.md
d/411/解释/v411-release-bundle-history-suite-design-evidence.html
```

## 一句话总结

v411 把 prompt suite design 不就绪从 project audit 继续推进到 release bundle，让最终发布证据也能说明 benchmark history 为什么需要 review。
