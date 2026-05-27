# v460 promoted receipt failure smoke plan check

## 本版目标和边界

v459 已经把 receipt contract failure smoke 封装成 CI wrapper，并写出 `ci_promoted_seed_receipt_contract_failure_smoke_plan.json`。
v460 的目标是给这个 plan 增加一层 contract check：不重跑 smoke，只读取 wrapper plan，验证子命令、failure-smoke 摘要和 artifact digest 是否仍然一致。

本版不改变四个 failure-smoke 场景，不提升模型训练能力，也不新建一条治理链。它只是把 v459 的 wrapper 产物变成可以被 CI 独立复核的证据单元。

## 前置链路

本版承接三层能力：

- v457：受控 failure smoke 矩阵能验证 summary-field、contract-profile、sidecar 三类失败归因。
- v458：failure smoke 接入 GitHub Actions，并由 CI workflow hygiene 检查执行顺序。
- v459：CI 调用改为 wrapper，并记录 child command、return code、summary 和 artifact digest。

v460 补上的位置是：

```text
assurance smoke
  -> receipt failure-smoke wrapper
  -> receipt failure-smoke wrapper plan check
  -> downstream gates
  -> coverage
```

## 关键文件

- `scripts/check_ci_promoted_seed_receipt_contract_failure_smoke_plan.py`
  - 新增 checker CLI。
  - 输入可以是 wrapper 输出目录，也可以是 plan JSON。
  - 输出 JSON/text/Markdown/HTML 四种检查报告。
- `scripts/run_ci_promoted_seed_receipt_contract_failure_smoke.py`
  - 将默认 `source_handoff` 修正为仓库相对路径 `d/448/解释/promoted-handoff`。
  - 这个修正让默认 CI 调用与 v448 handoff sidecar 中记录的相对路径保持一致。
- `.github/workflows/ci.yml`
  - 在 wrapper 后新增 `Promoted seed receipt contract failure smoke plan check` step。
- `src/minigpt/ci_workflow_hygiene.py`
  - 新增 required command 和两条 order check。
  - 汇总字段新增 `promoted_seed_receipt_contract_failure_smoke_plan_check_*`。
- `src/minigpt/ci_workflow_hygiene_artifacts.py`
  - Markdown 和 HTML 报告显示新的 plan-check readiness。
- `tests/test_ci_promoted_seed_receipt_contract_failure_smoke_plan_check.py`
  - 覆盖通过、篡改 digest、篡改 return code、CLI `--require-pass` / `--no-fail`。
- `tests/test_ci_promoted_seed_receipt_contract_failure_smoke.py`
  - 增加默认 handoff 保持仓库相对路径的断言。
- `tests/test_ci_workflow.py`
  - 更新 CI hygiene 的 required step/order 数量和 readiness 断言。

## 核心数据结构

checker 输出的主结构是：

```json
{
  "status": "pass",
  "decision": "continue",
  "source_plan": "d/460/解释/receipt-failure-smoke-wrapper/ci_promoted_seed_receipt_contract_failure_smoke_plan.json",
  "source_handoff": "d/448/解释/promoted-handoff",
  "failed_count": 0,
  "artifact_failure_count": 0,
  "failure_smoke_summary": {},
  "artifacts": [],
  "checks": [],
  "issues": []
}
```

其中 `checks` 是逐项判断，`issues` 只从失败 check 派生。这样正常情况不会产生噪声；失败时能直接定位是 wrapper 字段、return code、summary 字段，还是 artifact digest 出错。

## 核心检查逻辑

`check_plan()` 做四类检查：

1. Wrapper 身份和结论：
   - `wrapper == run_ci_promoted_seed_receipt_contract_failure_smoke`
   - `status == pass`
   - `decision == receipt_contract_failure_smoke_verified`
2. Child command：
   - `receipt_contract_summary.returncode == 0`
   - `receipt_contract_failure_smoke.returncode == 0`
3. Failure-smoke summary：
   - `available=True`
   - `status=pass`
   - `scenario_count=4`
   - `verified_scenario_count=4`
   - `failed_verification_count=0`
4. Artifact digest：
   - 四个关键 artifact 必须存在。
   - 记录的 size 和当前文件 size 一致。
   - 记录的 SHA-256 必须是 64 位小写 hex。
   - 记录的 SHA-256 必须等于当前文件重新计算的 SHA-256。

这里的关键点是：checker 不信任 plan 里的 digest 结果本身，而是用 plan 记录的路径重新读文件、重新计算 SHA-256。

## 输入输出格式

CLI 入口：

```powershell
python -B scripts/check_ci_promoted_seed_receipt_contract_failure_smoke_plan.py <plan-or-dir> --out-dir <dir> --require-pass
```

输出文件：

- `ci_promoted_seed_receipt_contract_failure_smoke_plan_check.json`
- `ci_promoted_seed_receipt_contract_failure_smoke_plan_check.txt`
- `ci_promoted_seed_receipt_contract_failure_smoke_plan_check.md`
- `ci_promoted_seed_receipt_contract_failure_smoke_plan_check.html`

`--require-pass` 明确要求失败时返回 `1`；`--no-fail` 则允许只写报告不让进程失败，便于本地排查。

## CI Workflow Hygiene 角色

v460 后 CI hygiene 的新顺序约束是：

- wrapper 必须在 assurance smoke 之后。
- plan check 必须在 wrapper 之后。
- wrapper 和 plan check 都必须在 coverage 之前。

因此 `check_ci_workflow_hygiene.py` 的报告会出现：

```text
promoted_seed_receipt_contract_failure_smoke_plan_check_present=True
promoted_seed_receipt_contract_failure_smoke_plan_check_order_ready=True
promoted_seed_receipt_contract_failure_smoke_plan_check_ready=True
```

这让 CI 结构本身也能证明 plan-check gate 没有被遗漏或放到 coverage 之后。

## 测试覆盖

本版 focused tests 覆盖：

- 合法 wrapper 输出能通过 plan check。
- 输出 sidecar 包含 JSON/text/Markdown/HTML。
- 手动篡改 `failure_smoke_json.sha256` 后，`artifact:failure_smoke_json:sha256` 失败。
- 手动篡改 child command return code 后，`--require-pass` 返回 `1`，`--no-fail` 返回 `0`。
- 默认 wrapper handoff 路径保持相对路径，避免与 v448 sidecar 内的相对路径 contract 冲突。
- CI workflow hygiene 更新到 `required_step_count=13`、`required_order_count=13`，并识别新的 plan-check readiness。
- 全量 pytest 最终为 `792 passed`，source encoding hygiene 为 `source_count=362`、`clean_count=362`。

## 运行证据

`d/460` 保存本版证据：

- `解释/receipt-failure-smoke-wrapper/`
  - v459 wrapper 输出和 plan。
- `解释/receipt-failure-smoke-plan-check/`
  - v460 plan-check 输出。
- `解释/ci-workflow-hygiene/`
  - 新 CI step 和新 order checks 的 hygiene 报告。
- `图片/01-receipt-wrapper-plan-check.png`
  - Playwright MCP 截图，显示 `Status=pass`、`Failed=0`、`Artifacts=4`。
- `解释/playwright_receipt_wrapper_plan_check_snapshot.md`
  - Playwright MCP 可访问性快照。

## 一句话总结

v460 把 receipt failure-smoke CI wrapper 从“会写 plan”推进到“plan 可被独立复核”，让 return code、summary 和 artifact digest 都成为 CI 可验证的 contract。
