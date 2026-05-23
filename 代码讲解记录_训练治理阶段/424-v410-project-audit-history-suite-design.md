# v410 project audit benchmark history suite design

## 本版目标和边界

v410 的目标是把 v408 写入 benchmark history ledger、v409 已进入 maturity narrative 的 suite-design readiness 继续接到 project audit。这样发布审计层不只看到 benchmark history 的普通 ready/review/regression，还能直接看到 prompt suite design 是否不适合比较。

本版不新增治理链，不训练 checkpoint，不改变 benchmark scorecard 的打分逻辑，也不扩展 release gate。它只让 project audit 消费已有 history 字段，并把这些字段展示到 check detail、summary、Markdown/HTML 和 CLI stdout。

## 前置能力

本版承接：

- v406：scorecard comparison 记录 `eval_suite_design_comparison_status`。
- v407：scorecard decision 把 suite-design not-ready 转成 review/remediation。
- v408：benchmark history 记录 `suite_design_non_comparison_ready_entry_count` 和 `design_comparison_changed_entry_count`。
- v409：maturity narrative 消费这些 history 字段。

v410 位于项目审计层，负责让 release-style audit 也能保留这条 prompt-suite 设计边界。

## 关键文件

### `src/minigpt/project_audit_contexts.py`

`build_benchmark_history_context()` 新增两个字段：

```text
suite_design_non_comparison_ready_entry_count
design_comparison_changed_entry_count
```

缺失 benchmark history 时，这两个字段返回 `None`；读取真实 history 时，从 `summary` 中取值。

`build_benchmark_history_check()` 现在会把 `suite_design_non_comparison_ready_entry_count > 0` 当作 warning 信号，并在 detail 中输出：

```text
suite_design_not_ready=<n>
design_comparison_changed=<n>
```

这让审计报告中的 benchmark history check 能解释：warning 是否来自普通回归、readiness requirement，还是来自 suite-design comparison readiness。

### `src/minigpt/project_audit.py`

project audit summary 新增：

```text
benchmark_history_suite_design_non_comparison_ready_entries
benchmark_history_design_comparison_changed_entries
```

`_benchmark_history_status()` 的 regression key 也包含 `suite_design_non_comparison_ready_entry_count`，因此只要 benchmark history 里出现非 comparison-ready suite design，audit status 就会进入 `warn`。

### `src/minigpt/project_audit_artifacts.py`

Markdown Summary 表新增：

```text
Benchmark history suite-design not-ready
Benchmark history design changes
```

HTML stats 新增：

```text
Bench design review
Bench design changes
```

这些字段用于审阅和截图，不是新的模型质量证据。

### `scripts/audit_project.py`

CLI stdout 新增：

```text
benchmark_history_suite_design_non_comparison_ready_entries
benchmark_history_design_comparison_changed_entries
```

自动化日志可以不用打开 JSON，就确认 project audit 是否接收到了 history 层的 suite-design readiness。

### `tests/test_project_audit.py`

测试 helper `make_benchmark_history()` 增加 `suite_design_status` 参数。默认 `pass` 时 summary 里的两个计数都是 `0`；传入 `warn` 时，history 会模拟：

```text
ready_count = 0
suite_design_non_comparison_ready_entry_count = 1
design_comparison_changed_entry_count = 1
readiness failed reason = suite_design_non_comparison_ready_entries
latest boundary = suite-design-not-comparison-ready
```

新增和更新的断言覆盖：

- 干净 benchmark history 在 audit summary/context 中显示 suite-design 计数为 `0`。
- suite-design not-ready history 会让 project audit 进入 `warn`。
- check detail 包含 `suite_design_not_ready=1` 和 `design_comparison_changed=1`。
- Markdown/HTML 渲染包含新增字段。
- `scripts/audit_project.py` stdout 打印新增字段。
- 直接调用 context/check helpers 时，缺失输入仍保持稳定的 `None`/`warn` 语义。

## 输入输出

输入仍是 project audit 原有输入：

```text
registry.json
model_card.json
request_history_summary.json
benchmark_history.json
ci_workflow_hygiene.json
test_coverage_report.json
```

输出新增字段：

```text
project_audit.json
  summary.benchmark_history_suite_design_non_comparison_ready_entries
  summary.benchmark_history_design_comparison_changed_entries
  benchmark_history_context.suite_design_non_comparison_ready_entry_count
  benchmark_history_context.design_comparison_changed_entry_count

project_audit.md/html
  Benchmark history suite-design not-ready
  Bench design review

CLI stdout
  benchmark_history_suite_design_non_comparison_ready_entries
  benchmark_history_design_comparison_changed_entries
```

这些字段属于审计解释证据，只说明 repeated benchmark evidence 的边界，不证明模型能力已经达到生产质量。

## 测试覆盖

定向验证命令：

```text
python -m pytest tests\test_project_audit.py -q
python -m py_compile src\minigpt\project_audit_contexts.py src\minigpt\project_audit.py src\minigpt\project_audit_artifacts.py scripts\audit_project.py tests\test_project_audit.py
```

完整验证还包括全量 pytest、source encoding hygiene 和 `git diff --check`。

## 运行证据

运行截图与说明归档在：

```text
d/410/图片/01-project-audit-history-suite-design-evidence.png
d/410/解释/说明.md
d/410/解释/v410-project-audit-history-suite-design-evidence.html
```

## 一句话总结

v410 把 prompt suite design 不就绪从 benchmark history 继续推进到 project audit，让项目审计也能直接说明“历史 benchmark 证据为什么还不能当成干净模型提升证据”。
