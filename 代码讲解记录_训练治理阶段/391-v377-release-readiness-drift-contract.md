# v377 release readiness drift contract 代码讲解

## 本版目标和边界

v377 的目标是给 release readiness comparison 的 benchmark-history readiness failed-reason drift 字段补一层只读契约检查。

v373-v376 已经让 added、removed、recovered、mixed 进入 comparison、registry、maturity summary 和 maturity narrative。问题在于：这些字段一旦被下游模块消费，就需要一个独立检查器证明它们仍然和原始 baseline/compared reason lists 自洽。

本版不新增 failed-reason drift 的业务语义，不改变 comparison 报告 schema，也不扩大模型质量声明。它只做一件事：从源 reason list 重新推导契约，再检查现有报告字段是否一致。

## 前置能力

本版承接 v373-v376：

- v373 让 failed-reason additions 成为 benchmark regression signal。
- v374 让 failed-reason removals 成为 recovery/stability evidence。
- v375 引入 `stable/regressed/recovered/mixed` drift status。
- v376 把 `mixed` 提升为 summary、registry、maturity 和 narrative 都能消费的 review signal。

v377 把这条线收口为可复跑检查：

```text
baseline failed reasons -> compared failed reasons
        |                         |
        v                         v
    recompute added / removed / drift status
        |
        v
compare with delta fields and summary fields
```

## 关键文件

### `src/minigpt/release_readiness_drift_contract.py`

这是本版核心模块，职责是校验已有 comparison JSON，而不是重新生成 comparison。

主要入口：

```python
check_release_readiness_drift_contract(comparison, comparison_path=None)
```

它读取：

```text
deltas[*].baseline_benchmark_history_readiness_requirement_failed_reasons
deltas[*].compared_benchmark_history_readiness_requirement_failed_reasons
summary.*
```

并重新计算：

```text
expected_added
expected_removed
expected_drift_status
expected_summary
```

drift status 的规则保持 v375-v376 语义：

```text
added + removed -> mixed
added only      -> regressed
removed only    -> recovered
no change       -> stable
```

模块输出一个检查报告：

```text
status: pass/fail
decision: continue/fix-release-readiness-drift-contract
delta_pass_count
delta_fail_count
expected_summary
actual_summary
issues
```

其中 `issues` 是机器可读的 blocker 列表，用于 CI 日志或本地排错。

### `scripts/check_release_readiness_drift_contract.py`

这是命令行入口。它接受两类输入：

```powershell
python scripts/check_release_readiness_drift_contract.py runs/release-readiness-comparison
python scripts/check_release_readiness_drift_contract.py runs/release-readiness-comparison/release_readiness_comparison.json
```

脚本会写出：

```text
release_readiness_drift_contract_check.json
release_readiness_drift_contract_check.txt
```

默认行为是契约失败时退出非零。`--no-fail` 可以只产出检查结果，不中断调用方。

### `tests/test_release_readiness_drift_contract.py`

测试使用最小 comparison fixture，覆盖四类关键边界：

- 合法 mixed drift 可以通过。
- summary mixed count 写错会失败。
- delta drift status 写错会失败。
- 输入目录能解析到 `release_readiness_comparison.json`。
- CLI 对无效契约返回非零，并写出 JSON/TXT 检查产物。

这些测试保护的是“报告字段自洽性”，不是模型输出质量。

## 输入输出格式

输入是 release readiness comparison JSON。检查器依赖 delta 中的源字段：

```json
{
  "baseline_benchmark_history_readiness_requirement_failed_reasons": ["insufficient_ready_entries", "legacy_fixture_gap"],
  "compared_benchmark_history_readiness_requirement_failed_reasons": ["insufficient_ready_entries", "tiny_smoke_only"]
}
```

推导出的 expected delta 是：

```json
{
  "expected_added": ["tiny_smoke_only"],
  "expected_removed": ["legacy_fixture_gap"],
  "expected_drift_status": "mixed"
}
```

如果报告里写成：

```json
{
  "benchmark_history_readiness_requirement_failed_reason_drift_status": "recovered"
}
```

检查器会产生：

```text
code=delta_failed_reason_drift_status_mismatch
target=deltas[0].benchmark_history_readiness_requirement_failed_reason_drift_status
```

## 测试覆盖

本版验证命令：

```powershell
python -m py_compile src/minigpt/release_readiness_drift_contract.py scripts/check_release_readiness_drift_contract.py
python -m pytest tests/test_release_readiness_drift_contract.py tests/test_release_readiness_comparison.py -q
```

阶段结果：

```text
19 passed
```

最终全量验证结果：

```text
677 passed
```

另外，`scripts/check_source_encoding.py` 验证 `310` 个源文件 clean，`0` 个 BOM，`0` 个语法错误，避免本版新增脚本或模块引入 CI 编码问题。

## 运行证据

运行证据归档在：

```text
d/377/图片/01-release-readiness-drift-contract-evidence.png
d/377/解释/说明.md
```

证据页展示了源 reason list、推导出的 added/removed/mixed，以及 CLI 失败保护边界。

## 一句话总结

v377 把 benchmark readiness failed-reason drift 从“下游会消费的报告字段”推进为“可独立复算和校验的契约”，降低后续字段迁移、手工修正或 summary 聚合错误造成静默错配的风险。
