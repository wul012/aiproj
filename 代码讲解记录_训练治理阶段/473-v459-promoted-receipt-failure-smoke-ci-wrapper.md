# v459 promoted receipt failure smoke CI wrapper

## 本版目标和边界

v458 把 receipt contract failure smoke 接入了 GitHub Actions，但 CI workflow 里直接写了两行长命令：先生成 receipt contract summary，再运行 failure smoke。v459 的目标是把这两行命令收束成一个稳定 wrapper，并记录可复核的 invocation plan。

本版不改变 failure smoke 场景，不改变 CI gate 的语义，也不新增新的治理链。它只把 v458 的 CI step 封装起来，让 workflow 更短、计划更清楚、产物 digest 更容易审计。

## 前置链路

本版承接：

- v457：受控失败矩阵能证明 summary-check failure family 归因正确。
- v458：failure smoke 已接入 CI workflow 和 CI workflow hygiene。

v459 将 CI step 从两行内联命令改成：

```yaml
- name: Promoted seed receipt contract failure smoke
  run: python -B scripts/run_ci_promoted_seed_receipt_contract_failure_smoke.py --out-dir runs/promoted-seed-receipt-contract-failure-smoke-ci --force
```

## 关键文件

- `scripts/run_ci_promoted_seed_receipt_contract_failure_smoke.py`
  - 新增 CI wrapper。
  - 执行 receipt contract summary 和 failure smoke 两个 child command。
  - 写出 `ci_promoted_seed_receipt_contract_failure_smoke_plan.json/txt`。
  - 记录 child command、return code、failure smoke summary 和 artifact digest。
- `.github/workflows/ci.yml`
  - CI 改为调用 wrapper。
- `src/minigpt/ci_workflow_hygiene.py`
  - required command 从两条内联命令收束为 wrapper command。
  - order 检查变为 assurance -> wrapper -> coverage。
- `tests/test_ci_promoted_seed_receipt_contract_failure_smoke.py`
  - 新增 wrapper 测试，验证 plan、return code、smoke summary 和 digest。
- `tests/test_ci_workflow.py`
  - 更新 CI hygiene 的 command/order 断言。

## 核心数据结构

`ci_promoted_seed_receipt_contract_failure_smoke_plan.json` 示例字段：

```json
{
  "wrapper": "run_ci_promoted_seed_receipt_contract_failure_smoke",
  "status": "pass",
  "decision": "receipt_contract_failure_smoke_verified",
  "source_handoff": "d/448/解释/promoted-handoff",
  "summary_out_dir": ".../receipt-contract-summary",
  "failure_smoke_out_dir": ".../receipt-contract-failure-smoke",
  "commands": [
    {"name": "receipt_contract_summary", "returncode": 0},
    {"name": "receipt_contract_failure_smoke", "returncode": 0}
  ],
  "failure_smoke_summary": {
    "status": "pass",
    "scenario_count": 4,
    "failed_verification_count": 0
  }
}
```

artifact digest 会记录：

- `contract_summary_json`
- `failure_smoke_json`
- `failure_smoke_csv`
- `failure_smoke_html`

## 运行流程

1. Wrapper 清理或创建 `--out-dir`。
2. 调用 `check_promoted_seed_handoff_receipt_contract.py` 生成 `receipt-contract-summary/`。
3. 若第一步通过，调用 failure smoke CLI 生成 `receipt-contract-failure-smoke/`。
4. 读取 failure smoke JSON，提取 status、scenario count、verification count。
5. 计算关键产物 SHA-256。
6. 写出 wrapper plan JSON/text。
7. 根据 plan status 返回退出码。

## 测试覆盖

Focused tests：

- Wrapper 能用测试 handoff 生成 summary 和 failure smoke。
- Plan status 为 `pass`。
- 两个 child command return code 均为 0。
- failure smoke summary 为 `status=pass`、`scenario_count=4`、`failed_verification_count=0`。
- artifact digest 中 summary JSON、failure smoke JSON/HTML 均存在。
- CI hygiene 识别 wrapper command，且 readiness 仍为 true。

本版最终验证会覆盖：

- `python -m py_compile` 新增 wrapper、CI hygiene 和测试。
- `python -m pytest tests/test_ci_workflow.py tests/test_ci_promoted_seed_receipt_contract_failure_smoke.py tests/test_promoted_training_scale_seed_handoff_receipt_contract_check_failure_smoke.py -q -o cache_dir=runs/pytest-cache-v459-focused`
  - `11 passed`。
- `python -m pytest tests -q -o cache_dir=runs/pytest-cache-v459`
  - `788 passed`。
- `python -B scripts/check_source_encoding.py --out-dir runs/source-encoding-hygiene-local`
  - `status=pass`，`source_count=360`，`clean_count=360`，`bom_count=0`，`syntax_error_count=0`。
- `git diff --check`
  - 通过；仅有 Windows 工作区 LF/CRLF 换行提示，没有 whitespace error。

## 运行证据

`d/459` 保存本版证据：

- `解释/receipt-failure-smoke-wrapper/`
  - Wrapper 输出，包括 plan JSON/text、receipt summary 子目录和 failure smoke 子目录。
- `解释/ci-workflow-hygiene/`
  - 新 wrapper 形态下的 CI hygiene 报告。
- `解释/receipt-failure-smoke-wrapper-stdout.txt`
  - Wrapper CLI 输出。
- `解释/ci-workflow-hygiene-stdout.txt`
  - 可见 `check_count=27`、`required_order_count=11`、`promoted_seed_receipt_contract_failure_smoke_ready=True`。
- `图片/01-ci-receipt-wrapper-ready.png`
  - Playwright MCP 截图，证明 CI hygiene HTML 显示 wrapper gate ready。
- `解释/playwright_ci_receipt_wrapper_snapshot.md`
  - Playwright MCP 可访问性快照。

## 一句话总结

v459 把 receipt failure smoke CI gate 从“可运行的两行命令”推进到“有 wrapper、有 plan、有 digest 的稳定 CI 调用单元”。
