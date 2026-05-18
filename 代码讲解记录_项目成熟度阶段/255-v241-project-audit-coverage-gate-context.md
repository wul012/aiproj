# v241 project audit coverage gate context 代码讲解

## 本版目标

v241 的目标是把 v240 的 coverage gate 结果接入 project audit，让覆盖率门禁不只停留在 CI 日志里，也能进入项目治理证据。

这版不是继续提高 coverage 阈值，也不是把 coverage gate 接进 release gate。它只先扩展 project audit：读取 `test_coverage_report.json`，把 coverage status、percent、fail-under 和 gap 放进 summary、checks、context、CLI 输出和 Markdown/HTML。

## 不做什么

本版不改 CI 的 `--fail-under 80`。

本版不让 coverage gate 失败直接导致 project audit fail；它和 CI workflow hygiene、request history 一样，先作为 review-level governance context。

本版不声称 coverage 通过等于模型质量通过。它只说明测试覆盖率门禁结果干净。

## 前置能力

v239 增加 coverage baseline report。

v240 给 coverage report 增加 `--fail-under 80` CI gate，报告里已经有：

```text
status
decision
line_coverage_percent
fail_under
coverage_gap
threshold_enabled
```

v241 消费这些字段，并把它们挂到 project audit。

## 关键文件

### `src/minigpt/project_audit_contexts.py`

新增：

```python
build_test_coverage_check(test_coverage_report, test_coverage_report_path)
build_test_coverage_context(test_coverage_report)
```

`build_test_coverage_check()` 负责把 coverage report 转成 audit check。

如果没有报告：

```text
id=test_coverage_report
status=warn
detail=test_coverage_report.json missing; coverage gate evidence was not summarized.
```

如果报告存在并且：

```text
summary.status == pass
summary.threshold_enabled == True
```

则 audit check 为 pass。

如果 coverage report 失败、缺 threshold，或只是 baseline 模式，则 audit check 为 warn。这个边界很重要：project audit 不直接替代 CI 失败，但会提示“覆盖率证据不适合当成干净门禁证据”。

`build_test_coverage_context()` 给 JSON 消费者提供机器可读字段：

```text
available
status
decision
line_coverage_percent
covered_lines
num_statements
missing_lines
file_count
threshold_enabled
fail_under
coverage_gap
```

### `src/minigpt/project_audit.py`

`build_project_audit()` 新增参数：

```python
test_coverage_report_path: str | Path | None = None
```

自动发现路径包括：

```text
<registry_dir>/test_coverage_report.json
<registry_dir>/test-coverage/test_coverage_report.json
<registry_dir_parent>/test-coverage/test_coverage_report.json
```

返回的 audit payload 新增：

```text
test_coverage_report_path
test_coverage_context
```

summary 新增：

```text
test_coverage_status
test_coverage_decision
test_coverage_percent
test_coverage_fail_under
test_coverage_gap
```

checks 新增一项：

```text
test_coverage_report
```

recommendations 也新增 coverage report 缺失或异常时的提示：

```text
Generate or review test_coverage_report.json before using coverage gate status as audit evidence.
```

### `src/minigpt/project_audit_artifacts.py`

Markdown summary 新增：

```text
Test coverage status
Test coverage percent
Test coverage fail under
Test coverage gap
```

HTML stats 新增：

```text
Coverage
Coverage %
```

这样人打开 audit 页面时，不需要翻 JSON 就能看到 coverage gate 是否干净。

### `scripts/audit_project.py`

CLI 新增参数：

```text
--test-coverage-report <path>
```

终端输出新增：

```text
test_coverage_status
test_coverage_percent
test_coverage_fail_under
test_coverage_gap
```

这让自动化日志也能直接看到 coverage gate 状态。

### `tests/test_project_audit.py`

新增 coverage report fixture：

```python
make_test_coverage_report(root, status="pass", threshold_enabled=True)
```

测试覆盖：

- 完整 project audit 能把 coverage pass 读进 summary/context/checks。
- coverage gate fail 时 audit 进入 warn，并显示 `coverage_gap`。
- context helper 能把 coverage report 转成 pass/warn/missing 三种语义。
- Markdown 输出包含 `Test coverage report`。

## 输入输出

输入：

- `registry.json`
- 可选 `model_card.json`
- 可选 `request_history_summary.json`
- 可选 `ci_workflow_hygiene.json`
- 新增可选 `test_coverage_report.json`

输出：

- `project_audit.json`
- `project_audit.md`
- `project_audit.html`
- CLI summary lines

## 运行证据

本版运行证据归档在 `c/241`：

- `图片/01-project-audit-coverage-tests.png`
- `图片/02-coverage-gate-smoke.png`
- `图片/03-project-audit-coverage-smoke.png`
- `图片/04-full-unittest.png`

smoke 中 coverage gate 结果：

```text
status=pass
decision=continue_with_coverage_gate
line_coverage_percent=90.17
fail_under=80.0
coverage_gap=0.0
```

project audit smoke 能读到：

```text
test_coverage_status=pass
test_coverage_percent=90.17
test_coverage_fail_under=80.0
test_coverage_gap=0.0
```

## 测试覆盖

本版验证了三层：

1. `tests.test_project_audit`：覆盖 audit schema、context helper、recommendation 和 Markdown artifact。
2. coverage gate smoke：真实生成 `test_coverage_report.json`。
3. project audit smoke：用 CLI 显式传入 coverage report，并确认 audit 输出 coverage summary。

全量 unittest 也通过，当前共 475 个测试。

## 证据链角色

v241 让 coverage gate 从“CI 执行结果”进入“项目审计上下文”。

它不会单独证明模型质量，但会让项目成熟度判断更完整：审计者可以在同一个 audit 中看到 registry/model card、CI workflow hygiene、request history、test coverage gate 这些治理证据。

## 一句话总结

v241 把覆盖率门禁纳入 project audit，让 aiproj 的测试治理从“CI 会拦截”推进到“治理报告也能解释 coverage gate 状态”。
