# v240 conservative coverage fail-under gate 代码讲解

## 本版目标

v240 的目标是把 v239 的 coverage baseline 推进成一个保守的 CI 覆盖率门禁。

v239 已经能记录覆盖率，但不会因为覆盖率下降而失败。v240 增加 `--fail-under`，让脚本可以在写出证据后按阈值返回失败码。CI 采用 `--fail-under 80`，低于本地约 90% 的 baseline，避免一开始就把阈值设得太激进。

## 不做什么

本版不把阈值设为 90%。

本版不改变 unittest 范围、测试框架或 coverage source 范围。

本版不声称覆盖率门禁等于模型质量门禁。它只保护测试触达率，不替代 benchmark、真实训练结果、生成质量或服务稳定性。

## 前置能力

v239 已提供：

- `scripts/run_test_coverage.py`
- `src/minigpt/test_coverage_report.py`
- coverage JSON/CSV/Markdown/HTML 输出
- CI 使用 coverage 脚本跑 unittest

v240 在这条链路上补一个最小的“门禁决策”层。

## 关键文件

### `src/minigpt/test_coverage_report.py`

`build_test_coverage_report()` 新增参数：

```python
fail_under: float | None = None
```

当 `fail_under` 为空时，报告仍保持 v239 的 baseline 语义：

```text
status=pass
decision=record_coverage_baseline
threshold_enabled=False
fail_under=None
coverage_gap=0.0
```

当传入阈值时，报告会比较：

```text
line_coverage_percent >= fail_under
```

通过时：

```text
status=pass
decision=continue_with_coverage_gate
coverage_gap=0.0
```

失败时：

```text
status=fail
decision=improve_test_coverage
coverage_gap=<fail_under - line_coverage_percent>
```

`_fail_under_value()` 会拒绝小于 0 或大于 100 的阈值，避免错误配置进入报告 schema。

Markdown/HTML 也新增展示：

- Status
- Fail under
- Coverage gap

这样人读报告时能看到这次是 baseline，还是 gate pass/fail。

### `scripts/run_test_coverage.py`

CLI 新增：

```text
--fail-under <percent>
```

脚本运行顺序保持关键边界：

1. 运行 unittest coverage。
2. 生成 coverage JSON。
3. 构建 test coverage report。
4. 写出 JSON/CSV/Markdown/HTML。
5. 打印 summary。
6. 如果 `summary.status != "pass"`，返回退出码 2。

这个顺序很重要：即使 coverage gate 失败，证据也已经写出，后续 CI artifact 或日志仍然可以解释为什么失败。

脚本还会在开始前快速拒绝非法阈值：

```text
--fail-under must be between 0 and 100
```

### `.github/workflows/ci.yml`

Unit tests 步骤改为：

```text
python -B scripts/run_test_coverage.py --out-dir runs/test-coverage-ci --fail-under 80
```

选择 80 的原因是保守：本地 v240 smoke 约 90.16%，80 能捕捉明显测试覆盖倒退，但不会因为小规模代码变化频繁误伤。

### `src/minigpt/ci_workflow_hygiene.py`

CI hygiene 的 required command fragments 从 3 项扩展到 4 项，新增：

```text
coverage_fail_under_gate: --fail-under 80
```

这保护 workflow 不只是“跑 coverage 脚本”，还必须保留覆盖率门禁阈值。

### `tests/test_test_coverage_report.py`

新增三类断言：

- coverage 达到阈值时，`decision=continue_with_coverage_gate`。
- coverage 低于阈值时，`decision=improve_test_coverage` 且 `coverage_gap` 正确。
- 非法阈值会抛出 `ValueError`。

原有 baseline 测试也补充断言 `fail_under=None` 和 `coverage_gap=0.0`，确保默认行为兼容。

### `tests/test_ci_workflow.py`

测试 fake workflow 中的 Unit tests 命令同步带上 `--fail-under 80`。

当前真实 workflow 的 CI hygiene 报告为：

```text
check_count=8
passed_check_count=8
missing_step_count=0
```

新增的第 8 个检查就是 coverage fail-under gate。

## 输入输出

输入：

- coverage.py 的 `coverage.json`
- 可选 `--fail-under`
- unittest 执行结果

输出：

- `test_coverage_report.json`
- `test_coverage_report.csv`
- `test_coverage_report.md`
- `test_coverage_report.html`
- CLI 退出码：通过为 0，覆盖率门禁失败为 2

## 运行证据

本版运行证据归档在 `c/240`：

- `图片/01-coverage-gate-tests.png`
- `图片/02-ci-workflow-hygiene.png`
- `图片/03-coverage-gate-smoke.png`
- `图片/04-full-unittest.png`

coverage gate smoke 结果：

```text
Ran 474 tests
status=pass
decision=continue_with_coverage_gate
line_coverage_percent=90.16
fail_under=80.0
coverage_gap=0.0
```

## 测试覆盖

本版验证了四层：

1. focused tests：覆盖 coverage gate schema、CI workflow hygiene 和阈值命令片段。
2. CI hygiene smoke：确认真实 workflow 8 项检查全部通过。
3. coverage gate smoke：真实跑 474 个测试并通过 `--fail-under 80`。
4. full unittest：再次确认全量测试通过。

## 证据链角色

v240 是测试治理门禁，不是发布治理总门禁。

它让 aiproj 具备“测试覆盖率明显倒退时 CI 能阻止”的基础能力，同时保留证据输出，方便后续查看最低覆盖文件和缺口。

后续如果要提高阈值，应先观察多轮 baseline，并优先补最低覆盖模块的 focused tests。

## 一句话总结

v240 把 coverage baseline 变成保守可执行的 CI gate，让 aiproj 的测试纪律从“可观察”推进到“可阻止明显倒退”。
