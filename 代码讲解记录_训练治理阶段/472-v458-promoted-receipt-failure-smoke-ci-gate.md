# v458 promoted receipt failure smoke CI gate

## 本版目标和边界

v457 新增了 receipt contract summary-check failure smoke matrix，但它仍然是本地/归档式验证。v458 把这个 smoke 接入 GitHub Actions，并让 CI workflow hygiene 检查它是否存在、是否排在正确位置。

本版不改变 promoted seed handoff 语义，不改变 failure smoke 的场景矩阵，也不新增新的模型训练链路。它只把 v457 的验证入口提升为 CI 可持续 gate。

## 前置链路

本版承接：

- v456：summary-check 能把失败归因到 `summary_field`、`contract_profile`、`sidecar`。
- v457：受控篡改矩阵能证明三类归因都按预期工作。

v458 将 v457 的 CLI 写入 CI：

```yaml
- name: Promoted seed receipt contract failure smoke
  run: |
    python -B scripts/check_promoted_seed_handoff_receipt_contract.py d/448/解释/promoted-handoff --out-dir runs/promoted-seed-receipt-contract-summary-ci --allow-stop
    python -B scripts/smoke_promoted_seed_handoff_receipt_contract_summary_check_failures.py runs/promoted-seed-receipt-contract-summary-ci --out-dir runs/promoted-seed-receipt-contract-summary-check-failure-smoke-ci --force
```

## 关键文件

- `.github/workflows/ci.yml`
  - 新增 `Promoted seed receipt contract failure smoke` step。
  - 先生成 receipt contract summary，再运行 failure smoke。
- `src/minigpt/ci_workflow_hygiene.py`
  - `REQUIRED_COMMAND_FRAGMENTS` 新增 receipt contract summary 与 failure smoke 命令。
  - `REQUIRED_COMMAND_ORDER` 新增 assurance -> summary -> failure smoke -> coverage 的顺序要求。
  - summary 新增 `promoted_seed_receipt_contract_failure_smoke_present`、`promoted_seed_receipt_contract_failure_smoke_order_ready`、`promoted_seed_receipt_contract_failure_smoke_ready`。
- `src/minigpt/ci_workflow_hygiene_artifacts.py`
  - Markdown/HTML 报告展示新增 readiness 字段。
- `scripts/check_ci_workflow_hygiene.py`
  - CLI 输出新增三项 readiness。
- `tests/test_ci_workflow.py`
  - 覆盖当前 CI workflow pass、缺失/错序场景和输出渲染。

## 核心字段

新增 summary 字段：

```json
{
  "promoted_seed_receipt_contract_failure_smoke_present": true,
  "promoted_seed_receipt_contract_failure_smoke_order_ready": true,
  "promoted_seed_receipt_contract_failure_smoke_ready": true
}
```

字段语义：

- `present`
  - CI workflow 中存在 `scripts/smoke_promoted_seed_handoff_receipt_contract_summary_check_failures.py`。
- `order_ready`
  - 三个顺序检查全部通过：
    - assurance smoke 先于 receipt contract summary。
    - receipt contract summary 先于 failure smoke。
    - failure smoke 先于 coverage。
- `ready`
  - `present and order_ready`。

## 运行流程

CI 中新增链路：

1. `check_promoted_seed_handoff_assurance_smoke.py`
2. `check_promoted_seed_handoff_receipt_contract.py`
3. `smoke_promoted_seed_handoff_receipt_contract_summary_check_failures.py`
4. 后续 tiny scorecard、boundary gate、release readiness、coverage

这保证 receipt contract summary-check 的失败归因不是只在版本归档里跑过，而是在 CI 中持续验证。

## 测试覆盖

Focused tests：

- `tests/test_ci_workflow.py`
  - 当前 CI workflow 必须通过新增 required command 和 order checks。
  - 老 runtime policy fixture 必须缺失新增 step。
  - assurance smoke 排在 coverage 后时，failure smoke before coverage 也会失败。
  - Markdown 输出包含 `promoted_seed_receipt_contract_failure_smoke_ready`。
- `tests/test_promoted_training_scale_seed_handoff_receipt_contract_check_failure_smoke.py`
  - 保留 v457 的四场景矩阵验证。

本版最终验证会覆盖：

- `python -m py_compile` 相关模块、脚本、测试。
- `python -m pytest tests/test_ci_workflow.py tests/test_promoted_training_scale_seed_handoff_receipt_contract_check_failure_smoke.py -q -o cache_dir=runs/pytest-cache-v458-focused`
  - `10 passed`。
- `python -m pytest tests -q -o cache_dir=runs/pytest-cache-v458`
  - `787 passed`。
- `python -B scripts/check_source_encoding.py --out-dir runs/source-encoding-hygiene-local`
  - `status=pass`，`source_count=358`，`clean_count=358`，`bom_count=0`，`syntax_error_count=0`。
- `git diff --check`
  - 通过；仅有 Windows 工作区 LF/CRLF 换行提示，没有 whitespace error。

## 运行证据

`d/458` 保存本版证据：

- `解释/receipt-contract-summary-ci/`
  - 模拟 CI 生成的 receipt contract summary。
- `解释/receipt-contract-failure-smoke-ci/`
  - 模拟 CI 运行的 failure smoke matrix。
- `解释/ci-workflow-hygiene/`
  - 新增 readiness 字段后的 CI hygiene JSON/CSV/Markdown/HTML。
- `解释/ci-workflow-hygiene-stdout.txt`
  - 可见 `promoted_seed_receipt_contract_failure_smoke_ready=True`。
- `图片/01-ci-receipt-failure-smoke-ready.png`
  - Playwright MCP 截图，证明 HTML 报告可见新增 CI readiness。
- `解释/playwright_ci_receipt_failure_smoke_snapshot.md`
  - Playwright MCP 可访问性快照。

## 一句话总结

v458 把 receipt contract summary-check 的失败归因验证从“版本证据”推进到“CI 持续门禁”，让这条治理链具备长期防回归能力。
