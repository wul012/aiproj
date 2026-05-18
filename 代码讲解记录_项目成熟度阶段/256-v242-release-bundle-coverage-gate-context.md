# v242 release bundle coverage gate context 代码讲解

## 本版目标

v242 的目标是把 v241 已经进入 project audit 的 coverage gate 结果继续带进 release bundle。

这版解决的问题是：发布交接时，reviewer 打开 release bundle 就能同时看到 registry、model card、project audit、request history、CI workflow hygiene 和 test coverage gate 的状态，不需要再回到 CI 日志里找覆盖率门禁。

## 不做什么

本版不改变 release gate 的通过规则。

本版不提高 `--fail-under 80` 阈值，也不把 coverage pass 解释成模型质量 pass。

本版不新增训练能力，只做 release handoff 证据链补齐。

## 前置能力

v239 增加非阻塞 coverage baseline report。

v240 增加保守的 `--fail-under 80` coverage gate。

v241 让 project audit 能读取 `test_coverage_report.json`，并在 audit summary、checks、context、CLI 输出和 Markdown/HTML 中展示 coverage status、percent、fail-under 和 gap。

v242 在这个基础上，让 release bundle 也消费同一个 coverage report 和 audit 中的 coverage summary。

## 关键文件

### `src/minigpt/release_bundle.py`

`build_release_bundle()` 新增参数：

```python
test_coverage_report_path: str | Path | None = None
```

路径解析新增 `_resolve_test_coverage_report_path()`，查找顺序是：

```text
显式 --test-coverage-report
audit.test_coverage_report_path
<registry_dir>/test_coverage_report.json
<registry_dir>/test-coverage/test_coverage_report.json
<registry_dir_parent>/test-coverage/test_coverage_report.json
```

这个顺序让 release bundle 可以直接复用 project audit 的 coverage 输入，也可以在没有 audit path 字段时从 registry 周边目录自动发现。

summary 新增字段：

```text
test_coverage_status
test_coverage_decision
test_coverage_percent
test_coverage_fail_under
test_coverage_gap
```

字段来源优先级是：

```text
project_audit.summary 中的 coverage 字段
test_coverage_report.summary 中的 coverage 字段
```

这样 bundle 可以保持和 audit 一致，同时在直接传入 coverage report 时仍然可用。

payload 还新增：

```text
inputs.test_coverage_report_path
test_coverage_context
```

`test_coverage_context` 是机器可读块，包含：

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

### release artifacts

`_collect_release_artifacts()` 会在 coverage report 存在时增加三类 artifact：

```text
test_coverage_report_json
test_coverage_report_md
test_coverage_report_html
```

它们分别指向：

```text
test_coverage_report.json
test_coverage_report.md
test_coverage_report.html
```

这三个产物不是训练输出，也不是模型质量证明。它们是 coverage gate 的发布交接证据，供 release bundle 的 JSON/Markdown/HTML 消费。

### `src/minigpt/release_bundle_artifacts.py`

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

这保证人读 release bundle 页面时，不需要打开 JSON 也能看到 coverage gate 是否干净。

### `scripts/build_release_bundle.py`

CLI 新增：

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

脚本层面的作用是让 CI、手工 smoke 或未来自动化任务能直接从控制台日志判断 coverage gate 是否进入了 bundle。

### `tests/test_release_bundle.py`

测试夹具新增 `test_coverage_report.json/md/html`。

重点断言包括：

- bundle summary 能显示 `test_coverage_status=pass`。
- bundle inputs 能记录显式 coverage report path。
- bundle artifacts 包含 `test_coverage_report_json` 和 `test_coverage_report_html`。
- bundle `test_coverage_context.coverage_gap == 0.0`。
- Markdown 输出包含 `Test coverage status`。

## 输入输出

输入：

```text
registry.json
model_card.json
project_audit.json
request_history_summary.json
ci_workflow_hygiene.json
test_coverage_report.json
```

输出：

```text
release_bundle.json
release_bundle.md
release_bundle.html
CLI summary lines
```

新增输出语义：

```text
release bundle summary 里可以直接看到 coverage gate 状态
release bundle artifacts 里可以追溯 coverage report 三件套
release bundle context 里可以机器读取 coverage gate 的计数和阈值
```

## 运行证据

本版运行证据归档在 `c/242`：

- `图片/01-release-bundle-tests.png`
- `图片/02-coverage-gate-smoke.png`
- `图片/03-release-bundle-coverage-smoke.png`
- `图片/04-full-unittest.png`

coverage gate smoke 输出：

```text
status=pass
decision=continue_with_coverage_gate
line_coverage_percent=90.15
fail_under=80.0
coverage_gap=0.0
```

release bundle smoke 输出：

```text
release_status=release-ready
audit_status=pass
request_history_status=pass
ci_workflow_status=pass
test_coverage_status=pass
test_coverage_percent=90.15
test_coverage_fail_under=80.0
test_coverage_gap=0.0
```

这个 smoke 使用最小但完整的 registry/model-card/request-history/CI/coverage/audit 输入，证明 v242 的 coverage context 可以跨脚本进入 release bundle。

## 测试覆盖

本版验证分四层：

1. `tests.test_release_bundle` 覆盖 bundle schema、summary、context、artifact key 和 Markdown 输出。
2. `tests.test_project_audit` 确认 v241 的 audit coverage context 仍然兼容 v242。
3. coverage gate smoke 真实运行全部 unittest 并生成 `test_coverage_report.json`。
4. 全量 unittest 通过，当前共 476 个测试。

## 证据链角色

v242 把 coverage gate 从 project audit 继续推进到 release bundle。

现在 release handoff 不只说明“项目审计通过”，还可以说明“审计所依赖的 coverage gate 报告存在、阈值启用、覆盖率高于 `fail_under`，且报告路径可追溯”。

## 一句话总结

v242 让 release bundle 成为 coverage-aware handoff：覆盖率门禁结果从 CI 和 project audit 进入发布交接包，但仍保持 review/evidence 语义，不夸大成模型能力证明。
