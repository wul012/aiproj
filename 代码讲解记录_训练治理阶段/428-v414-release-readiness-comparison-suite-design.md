# v414 release readiness comparison benchmark history suite design

## 本版目标和边界

v414 的目标是把 v413 进入 release readiness 的 benchmark-history suite-design 字段继续接到 comparison 层。这样 readiness comparison 不只比较 status、benchmark readiness requirement 和 failed reasons，也能看到 suite-design not-ready 和 design-comparison changed 的变化。

本版不重新定义 suite-design 质量，不新增治理链，不训练 checkpoint，也不扩展 comparison 到新的评审层。它只让比较报告消费已有 readiness 字段，并把这些字段写进 summary、delta、Markdown/HTML 和 CLI stdout。

## 前置能力

本版承接：

- v408：benchmark history ledger 保存 suite-design not-ready 和 design-change 计数。
- v410：project audit 消费 benchmark-history suite-design readiness。
- v411：release bundle 汇总这些计数。
- v412：release gate 将 suite-design not-ready 计数纳入 gate warning。
- v413：release readiness dashboard 继续消费这些字段。

v414 位于 comparison 层，负责把 release readiness 之间的 suite-design 差异带进比较结果。

## 关键文件

### `src/minigpt/release_readiness_comparison.py`

`_row_from_report()` 新增保留字段：

```text
benchmark_history_suite_design_non_comparison_ready_entries
benchmark_history_design_comparison_changed_entries
```

`_delta_from_baseline()` 新增两个 delta：

```text
benchmark_history_suite_design_non_comparison_ready_entries_delta
benchmark_history_design_comparison_changed_entries_delta
```

`_delta_explanation()` 现在会先描述 suite-design not-ready delta 和 design-comparison changed delta，再继续写 readiness requirement、failed reasons 和 boundary 变化。

`_summary()` 新增：

```text
benchmark_history_suite_design_non_comparison_ready_delta_count
benchmark_history_suite_design_non_comparison_ready_regression_count
benchmark_history_design_comparison_changed_delta_count
```

其中 suite-design not-ready 正向增量会被计入 benchmark-history regression。

`_recommendations()` 先检查 suite-design regression，再回退到通用 benchmark history regression 文案，这样推荐信息更贴近真正的设计边界问题。

### `src/minigpt/release_readiness_comparison_artifacts.py`

CSV 增加：

```text
benchmark_history_suite_design_non_comparison_ready_entries
benchmark_history_design_comparison_changed_entries
```

delta CSV 增加：

```text
benchmark_history_suite_design_non_comparison_ready_entries_delta
benchmark_history_design_comparison_changed_entries_delta
```

Markdown Summary / HTML stats / Readiness Matrix / Deltas 都增加对应列和统计项。

### `scripts/compare_release_readiness.py`

CLI stdout 新增输出：

```text
benchmark_history_suite_design_non_comparison_ready_delta_count
benchmark_history_suite_design_non_comparison_ready_regression_count
benchmark_history_design_comparison_changed_delta_count
benchmark_history_suite_design=<release>:<ready_count>:<design_change_count>
```

### `tests/test_release_readiness_comparison.py`

测试覆盖：

- suite-design not-ready 增量会被计入 regression。
- delta explanation 会打印 suite-design not-ready 和 design-comparison changed。
- CSV / delta CSV / Markdown / HTML 都包含新字段。
- CLI stdout 也打印 comparison 汇总和每行 suite-design 值。

## 输入输出

输入仍然是 release readiness JSON 对：

```text
release_readiness.json
release_readiness.json
```

输出新增字段：

```text
release_readiness_comparison.json
  summary.benchmark_history_suite_design_non_comparison_ready_delta_count
  summary.benchmark_history_suite_design_non_comparison_ready_regression_count
  summary.benchmark_history_design_comparison_changed_delta_count

release_readiness_comparison.csv / delta_csv / markdown / html
  suite-design not-ready 与 design-comparison changed 相关列

CLI stdout
  benchmark_history_suite_design_non_comparison_ready_delta_count
  benchmark_history_suite_design_non_comparison_ready_regression_count
  benchmark_history_design_comparison_changed_delta_count
```

## 流程说明

1. `build_release_readiness_comparison()` 读取多份 release readiness JSON。
2. `_row_from_report()` 将 readiness 层已经确认的 suite-design 字段带入 comparison row。
3. `_delta_from_baseline()` 计算 baseline 与 current 的 suite-design 差异。
4. `_summary()` 汇总 suite-design delta/regression 次数。
5. artifact writer 和 CLI 复用这些字段生成可审阅输出。

## 测试覆盖

定向验证命令：

```text
python -m pytest tests\test_release_readiness_comparison.py -q
```

结果：`17 passed`。

完整验证还包括：

```text
python -m py_compile src\minigpt\release_readiness_comparison.py src\minigpt\release_readiness_comparison_artifacts.py scripts\compare_release_readiness.py tests\test_release_readiness_comparison.py
python -m pytest -q
python -B scripts\check_source_encoding.py --out-dir runs\source-encoding-hygiene-v414
git diff --check
```

结果：全量 pytest `703 passed`，source encoding hygiene `status=pass` 且 `319` 个 source clean，`git diff --check` 无 whitespace error。

## 运行证据

运行截图与说明归档在：

```text
d/414/图片/01-release-readiness-comparison-suite-design-evidence.png
d/414/解释/说明.md
d/414/解释/v414-release-readiness-comparison-suite-design-evidence.html
```

## 一句话总结

v414 让 release readiness comparison 也能看见 suite-design not-ready 的变化，把 prompt-suite 设计边界完整带到对比层。
