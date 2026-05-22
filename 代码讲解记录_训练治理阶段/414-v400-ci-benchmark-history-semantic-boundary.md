# v400 CI benchmark-history semantic boundary 代码讲解

## 本版目标和边界

v400 的目标是让 CI tiny scorecard plan checker 不只检查 benchmark history 文件是否存在、大小和 hash 是否一致，还要读取 `benchmark_history.json` 的语义字段，直接暴露 tiny-smoke 边界。

本版不新增 artifact，不改变 CI wrapper 运行参数，不改变 benchmark history 生成逻辑，也不把 tiny-smoke 升级为真实 benchmark。它只让现有 plan checker 更会“读证据”。

## 前置能力

v398 让 tiny scorecard comparison smoke 写出 benchmark history。v399 把四个 history artifact 纳入 CI wrapper plan digest 和 checker。v400 在 v399 的基础上继续向前一步：

```text
artifact digest protection
        |
        +--> semantic review of benchmark_history.json
                |
                +--> evidence_kind
                +--> model_quality_claim
                +--> readiness requirement
                +--> failed reasons
                +--> latest boundary
```

## 关键文件

### `scripts/check_ci_tiny_scorecard_plan.py`

新增 `_benchmark_history_review()`：

```text
input: summary_digest.artifacts.benchmark_history_json
output: benchmark_history semantic summary
```

它会读取 plan digest 里记录的 `benchmark_history_json.path`，解析 JSON，并提取：

```text
available
parse_status
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

新增 `_benchmark_history_boundary_issues()`，只对 `run_ci_tiny_scorecard_comparison_smoke` wrapper 强制 tiny-smoke 边界：

- `evidence_kind` 必须是 `tiny-smoke`；
- `model_quality_claim` 必须是 `not_claimed`；
- `readiness_requirement_failed_reasons` 必须包含 `not_real_benchmark_evidence`。

如果不满足，checker 会输出：

```text
benchmark_history_kind_mismatch
benchmark_history_model_claim_unexpected
benchmark_history_boundary_reason_missing
```

`render_check()` 同步输出 shell-readable 语义字段，例如：

```text
benchmark_history_evidence_kind=tiny-smoke
benchmark_history_model_quality_claim=not_claimed
benchmark_history_readiness_requirement_status=fail
benchmark_history_readiness_requirement_failed_reasons=insufficient_ready_entries,not_real_benchmark_evidence
benchmark_history_latest_boundary=tiny-smoke-plumbing-evidence
```

### `tests/test_ci_tiny_scorecard_plan_check.py`

测试新增 `write_history_artifacts()`，用一个最小但真实的 tiny-smoke history fixture 替代原来的空壳 JSON。

覆盖点：

- 正常 tiny-smoke history 下，checker `status=pass`；
- JSON/text 报告都暴露 evidence kind、model claim 和 failed reasons；
- 修改 summary artifact 仍能触发旧的 digest mismatch；
- CI wrapper 如果记录了 `real-benchmark` + `candidate_evidence`，checker 会失败；
- 真实 wrapper smoke -> plan checker 链路中，报告能读到 `tiny-smoke`、`not_claimed`、`fail` 和 `not_real_benchmark_evidence`。

## 输入输出格式

输入仍是：

```text
ci_tiny_scorecard_smoke_plan.json
```

输出仍是：

```text
ci_tiny_scorecard_smoke_plan_check.json
ci_tiny_scorecard_smoke_plan_check.txt
```

JSON 里新增顶层：

```text
benchmark_history
```

这是对 benchmark history 的语义摘要，不替代原始 `benchmark_history.json`。

## 运行流程

```text
scripts/check_ci_tiny_scorecard_plan.py
        |
        +--> load ci_tiny_scorecard_smoke_plan.json
        +--> validate eight artifact digests
        +--> read benchmark_history.json
        +--> summarize tiny-smoke boundary semantics
        +--> fail if CI wrapper history claims real benchmark quality
        +--> write plan-check JSON/TXT
```

## 测试覆盖

本版定向验证：

```text
python -m py_compile scripts/check_ci_tiny_scorecard_plan.py tests/test_ci_tiny_scorecard_plan_check.py
python -m pytest tests/test_ci_tiny_scorecard_plan_check.py -q
python -m pytest tests/test_ci_tiny_scorecard_smoke.py tests/test_ci_tiny_scorecard_plan_check.py -q
```

全量收口继续执行：

```text
python -m pytest -q
python -B scripts/check_source_encoding.py --out-dir runs/source-encoding-hygiene-v400
git diff --check
```

## 证据归档

运行截图和说明放在：

```text
d/400/图片
d/400/解释/说明.md
```

`d/400/解释/v400-ci-benchmark-history-semantic-boundary-evidence.html` 是给 Playwright MCP 截图的静态证据页。

## 一句话总结

v400 让 CI plan checker 从“确认 benchmark history 文件未漂移”升级为“确认 benchmark history 仍然只是 tiny-smoke 链路证据，没有误冒充真实模型质量”。
