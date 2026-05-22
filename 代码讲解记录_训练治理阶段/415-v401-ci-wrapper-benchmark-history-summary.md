# v401 CI wrapper benchmark-history summary 代码讲解

## 本版目标和边界

v401 的目标是让 CI tiny scorecard wrapper 生成的 invocation plan 自己携带 benchmark-history 语义摘要。v400 已经让 plan checker 重新读取 `benchmark_history.json` 并保护 tiny-smoke 边界；v401 让 plan 文件本身也能说明这条边界，方便 CI 日志、交接和人工审阅。

本版不新增 CI 步骤，不新增 artifact 文件，不改变 tiny smoke 训练预算，也不改变 checker 的边界判定。它只是把已经生成的 benchmark history 摘要写回 wrapper plan。

## 前置能力

v398 生成 benchmark history。v399 保护 history artifact digest。v400 在 checker 中读取 history 语义。v401 把相同语义提前写进 plan：

```text
run_ci_tiny_scorecard_comparison_smoke.py
        |
        +--> run tiny smoke
        +--> build summary digest
        +--> build benchmark_history_summary
        +--> write ci_tiny_scorecard_smoke_plan.json/txt
```

## 关键文件

### `scripts/run_ci_tiny_scorecard_comparison_smoke.py`

新增 `build_benchmark_history_summary(out_dir)`：

```text
input: <out-dir>/benchmark-history/benchmark_history.json
output: benchmark_history_summary
```

如果文件缺失，返回：

```text
available=false
parse_status=missing
path=<expected path>
```

如果 JSON 无法解析，返回：

```text
available=false
parse_status=invalid_json
error=<parse error>
```

如果解析成功，写出：

```text
available
parse_status
path
evidence_kind
entry_count
ready_count
model_quality_claim
readiness_requirement_status
readiness_requirement_decision
readiness_requirement_exit_code
readiness_requirement_failed_reasons
latest_boundary
boundary_values
```

`build_invocation_plan()` 现在把该摘要写入：

```text
benchmark_history_summary
```

`render_invocation_plan()` 同步输出 line-oriented 字段：

```text
benchmark_history_available=True
benchmark_history_parse_status=pass
benchmark_history_evidence_kind=tiny-smoke
benchmark_history_model_quality_claim=not_claimed
benchmark_history_readiness_requirement_status=fail
benchmark_history_readiness_requirement_failed_reasons=insufficient_ready_entries,not_real_benchmark_evidence
benchmark_history_latest_boundary=tiny-smoke-plumbing-evidence
```

### `tests/test_ci_tiny_scorecard_smoke.py`

测试新增三个重点：

- 缺失 history 时，plan 明确记录 `parse_status=missing`；
- fixture-level tiny-smoke history 能被读出 evidence kind、model claim、failed reasons 和 latest boundary；
- 真实 wrapper smoke 产出的 plan JSON/TXT 都包含 tiny-smoke boundary summary。

## 输入输出格式

输入来自同一 wrapper 输出目录：

```text
benchmark-history/benchmark_history.json
```

输出仍然是既有文件：

```text
ci_tiny_scorecard_smoke_plan.json
ci_tiny_scorecard_smoke_plan.txt
```

本版只在 JSON 里新增 `benchmark_history_summary`，在文本里新增对应 key/value 行。

## 运行流程

```text
main()
        |
        +--> subprocess.run(tiny scorecard comparison smoke)
        +--> build_summary_digest()
        +--> build_invocation_plan()
                |
                +--> build_benchmark_history_summary(out_dir)
        +--> write_invocation_plan()
```

## 测试覆盖

定向验证：

```text
python -m py_compile scripts/run_ci_tiny_scorecard_comparison_smoke.py tests/test_ci_tiny_scorecard_smoke.py
python -m pytest tests/test_ci_tiny_scorecard_smoke.py -q
python -m pytest tests/test_ci_tiny_scorecard_smoke.py tests/test_ci_tiny_scorecard_plan_check.py -q
```

全量收口继续执行：

```text
python -m pytest -q
python -B scripts/check_source_encoding.py --out-dir runs/source-encoding-hygiene-v401
git diff --check
```

## 证据归档

运行截图和说明放在：

```text
d/401/图片
d/401/解释/说明.md
```

`d/401/解释/v401-ci-wrapper-benchmark-history-summary-evidence.html` 是给 Playwright MCP 截图的静态证据页。

## 一句话总结

v401 让 CI wrapper plan 自己能讲清 benchmark history 的 tiny-smoke 边界，再由 v400 checker 去复核原始 artifact，形成更完整的交接闭环。
