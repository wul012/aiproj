# v413 release readiness benchmark history suite design

## 本版目标和边界

v413 的目标是把 v412 进入 release gate 的 benchmark-history suite-design readiness 继续接到 release readiness dashboard。这样发布准备面板不只看到 benchmark history 是否 pass、readiness requirement 是否 pass，还能看到 prompt suite design 是否仍有 non-comparison-ready 条目。

本版不新增治理链，不训练 checkpoint，不扩展 benchmark prompt suite，也不改变 release readiness comparison。它只消费上游已有字段，并把这些字段推进到 readiness summary、benchmark panel、Markdown/HTML 和 CLI stdout。

## 前置能力

本版承接：

- v408：benchmark history ledger 保存 suite-design not-ready 和 design-change 计数。
- v410：project audit 消费 benchmark-history suite-design readiness。
- v411：release bundle 汇总这些计数，并处理新 history 与旧 audit summary 的优先级。
- v412：release gate 将 suite-design not-ready 计数纳入 gate warning。

v413 位于 release readiness 层，负责在发布准备看板里保留这条 prompt-suite 设计边界。

## 关键文件

### `src/minigpt/release_readiness.py`

`_benchmark_history_summary()` 新增两个 summary 字段：

```text
benchmark_history_suite_design_non_comparison_ready_entries
benchmark_history_design_comparison_changed_entries
```

字段来源仍遵循 readiness 的既有优先级：

```text
release gate summary -> release bundle summary
```

也就是说，readiness 不重新解析 benchmark history ledger，而是消费 gate/bundle 已经确认过的发布证据。

`_benchmark_history_panel()` 新增 detail 片段：

```text
suite_design_not_ready=<n>
design_comparison_changed=<n>
```

`_benchmark_history_panel_status()` 新增判断：

```text
if suite_design_not_ready > 0:
    return "warn"
```

这让 `benchmark_history_status=pass` 的情况下，仍然可以因为 prompt suite design 不适合比较而进入 release readiness review。

### `src/minigpt/release_readiness_artifacts.py`

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

这些输出用于人工审阅、归档截图和后续证据链引用，不代表模型本身达到生产质量。

### `scripts/build_release_readiness.py`

CLI stdout 新增：

```text
benchmark_history_suite_design_non_comparison_ready_entries=<n>
benchmark_history_design_comparison_changed_entries=<n>
```

这样 CI 日志或本地命令输出不用打开 JSON，也能看到 readiness 是否继承了 suite-design 风险。

### `tests/test_release_readiness.py`

测试 fixture 增加 suite-design 参数：

```text
benchmark_history_suite_design_non_comparison_ready_entries
benchmark_history_design_comparison_changed_entries
```

新增和更新的测试覆盖：

- 默认 ready 输入下两个字段都是 `0`，不影响 release readiness `ready`。
- suite-design not-ready count 大于 `0` 时，benchmark history panel 进入 `warn`，整体 readiness 进入 `review`。
- panel detail 包含 `suite_design_not_ready=1` 和 `design_comparison_changed=2`。
- Markdown 输出包含 `Benchmark history suite-design not-ready`。
- HTML 输出包含 `Bench design review`。
- `scripts/build_release_readiness.py` stdout 输出两个新增字段。

## 输入输出

输入仍是 release readiness 原有证据：

```text
release_bundle.json
gate_report.json
project_audit.json
request_history_summary.json
maturity_summary.json
ci_workflow_hygiene.json
test_coverage_report.json
```

输出新增字段：

```text
release_readiness.json
  summary.benchmark_history_suite_design_non_comparison_ready_entries
  summary.benchmark_history_design_comparison_changed_entries

release_readiness.md/html
  Benchmark history suite-design not-ready
  Bench design review

CLI stdout
  benchmark_history_suite_design_non_comparison_ready_entries
  benchmark_history_design_comparison_changed_entries
```

## 流程说明

1. `build_release_readiness_dashboard()` 读取 release bundle，并尝试定位 gate、audit、request history、maturity、CI workflow 和 test coverage 证据。
2. `_summary()` 调用 `_benchmark_history_summary()`，从 gate summary 优先读取 benchmark-history suite-design 计数，缺失时回退 bundle summary。
3. `_benchmark_history_panel()` 生成 benchmark history panel detail，展示 status、ready/review/blocked、regression、readiness requirement、suite-design not-ready 和 design-change。
4. `_benchmark_history_panel_status()` 根据 readiness requirement failure、exit code 和 suite-design not-ready count 决定是否 `warn`。
5. artifact writer 把新增字段写入 Markdown/HTML；CLI 把新增字段打印到 stdout。

## 测试覆盖

定向验证命令：

```text
python -m pytest tests\test_release_readiness.py -q
```

结果：`14 passed`。

完整验证还包括：

```text
python -m py_compile src\minigpt\release_readiness.py src\minigpt\release_readiness_artifacts.py scripts\build_release_readiness.py tests\test_release_readiness.py
python -m pytest -q
python -B scripts\check_source_encoding.py --out-dir runs\source-encoding-hygiene-v413
git diff --check
```

结果：全量 pytest `701 passed`，source encoding hygiene `status=pass` 且 `319` 个 source clean，`git diff --check` 无 whitespace error。

## 运行证据

运行截图与说明归档在：

```text
d/413/图片/01-release-readiness-history-suite-design-evidence.png
d/413/解释/说明.md
d/413/解释/v413-release-readiness-history-suite-design-evidence.html
```

## 一句话总结

v413 把 prompt suite design 不就绪继续推进到 release readiness，让最终发布准备面板也能明确提示 benchmark history 仍需要 review。
