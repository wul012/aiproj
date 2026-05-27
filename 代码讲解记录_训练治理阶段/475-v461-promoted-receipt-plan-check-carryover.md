# v461 promoted receipt plan-check carryover

## 本版目标和边界

v460 已经把 receipt failure-smoke CI wrapper plan 做成可独立复核的 contract check，并在 CI workflow hygiene 中产出：

```text
promoted_seed_receipt_contract_failure_smoke_plan_check_ready=True
```

v461 的目标是把这个 readiness 结果继续带到 project audit、release bundle、release readiness 三层发布证据里。这样读最终发布包时，不需要回头打开 CI hygiene 原始 JSON，也能确认 receipt failure-smoke wrapper plan check 已经存在、顺序正确、并通过。

本版不新增治理链，不重跑 failure smoke，不改变 v460 的 checker 判定逻辑，也不提升模型训练能力。它只做字段贯通、报告可见性和测试兜底。

## 前置链路

本版承接 v458-v460 的 CI 证据链：

```text
v458: failure smoke 接入 CI
  -> v459: CI wrapper 记录 plan
  -> v460: plan check 复核 wrapper 产物
  -> v461: plan-check readiness 进入发布侧证据
```

v461 补上的位置是：

```text
CI workflow hygiene summary
  -> project audit summary/context
  -> release bundle summary/context
  -> release readiness summary/panel
```

## 关键文件

- `src/minigpt/project_audit_contexts.py`
  - 在 CI workflow context 和 check evidence 中保留 receipt plan-check 的 present/order/ready 三个字段。
  - audit check detail 追加 `promoted_seed_receipt_contract_failure_smoke_plan_check_ready=...`。
- `src/minigpt/project_audit.py`
  - 在 audit summary 中新增 `ci_promoted_seed_receipt_contract_failure_smoke_plan_check_ready`。
- `src/minigpt/project_audit_artifacts.py`
  - Markdown 表格显示 `CI receipt failure-smoke plan check`。
  - HTML 指标卡显示 `CI receipt plan`。
- `src/minigpt/release_bundle_contexts.py`
  - release bundle 的 CI context 从 CI hygiene 或 audit context 中取 receipt plan-check 字段。
- `src/minigpt/release_bundle_support.py`
  - release bundle summary 新增 `ci_workflow_promoted_seed_receipt_contract_failure_smoke_plan_check_ready`。
- `src/minigpt/release_bundle_artifacts.py`
  - release bundle Markdown/HTML 显示 receipt plan-check readiness。
- `src/minigpt/release_readiness.py`
  - release readiness summary 和 CI Workflow Hygiene panel 显示 receipt plan-check readiness。
  - 当原始 CI hygiene JSON 缺失时，也能从 bundle summary/context fallback 取值。
- `src/minigpt/release_readiness_artifacts.py`
  - readiness Markdown/HTML 显示 receipt plan-check readiness。
- `scripts/audit_project.py`
  - CLI 输出 `ci_promoted_seed_receipt_contract_failure_smoke_plan_check_ready`。
- `scripts/build_release_bundle.py`
  - CLI 输出 `ci_workflow_promoted_seed_receipt_contract_failure_smoke_plan_check_ready`。
- `scripts/build_release_readiness.py`
  - CLI 输出最终 readiness 层的 receipt plan-check readiness。

## 核心字段语义

CI hygiene 原始字段仍然是：

```json
{
  "promoted_seed_receipt_contract_failure_smoke_plan_check_present": true,
  "promoted_seed_receipt_contract_failure_smoke_plan_check_order_ready": true,
  "promoted_seed_receipt_contract_failure_smoke_plan_check_ready": true
}
```

audit summary 使用 `ci_` 前缀：

```json
{
  "ci_promoted_seed_receipt_contract_failure_smoke_plan_check_ready": true
}
```

release bundle 和 release readiness summary 使用 `ci_workflow_` 前缀：

```json
{
  "ci_workflow_promoted_seed_receipt_contract_failure_smoke_plan_check_ready": true
}
```

这个命名沿用项目里已有的规则：audit 代表项目审计视角，release bundle/readiness 代表 CI workflow 视角。

## 运行流程

1. `build_ci_workflow_hygiene_check()` 读取 CI hygiene summary。
2. audit context 保留 present/order/ready 三个细节字段。
3. `_summarize_checks()` 把 ready 字段提升到 audit summary。
4. release bundle summary 优先从直接传入的 CI hygiene summary 取值；如果没有，则从 audit CI context 或 audit summary 取值。
5. release readiness summary 优先从直接传入的 CI hygiene summary 取值；如果没有，则从 bundle summary/context 取值。
6. Markdown/HTML/CLI 三类输出都显示同一个 readiness 结论。

`first_present()` 是这条链路的关键 helper：它避免 `False` 被当成缺省值跳过，因此未来如果 plan check 失败，`False` 会被如实带到下游，而不是误写成 `None` 或被 audit 旧值覆盖。

## 测试覆盖

本版 focused tests 覆盖三层：

- `tests/test_project_audit.py`
  - CI hygiene pass 时 audit summary/context 都出现 receipt plan-check ready。
  - CI hygiene fail 时 audit check detail 和 evidence 明确显示 `False`。
  - Markdown/HTML/CLI 输出包含新字段。
- `tests/test_release_bundle.py`
  - release bundle 从 CI hygiene 和 audit context 中带出新字段。
  - 显式传入 CI hygiene path 时字段仍为 `True`。
  - Markdown/HTML/CLI 输出包含新字段。
- `tests/test_release_readiness.py`
  - 原始 CI hygiene JSON 存在时，readiness summary 和 panel 都显示新字段。
  - 原始 CI hygiene JSON 缺失时，从 bundle summary/context fallback 仍能显示新字段。
  - Markdown/HTML/CLI 输出包含新字段。

Focused 验证结果：

```text
39 passed
```

## 运行证据

`d/461` 保存本版证据：

- `解释/project-audit-carryover/`
  - audit JSON/Markdown/HTML，显示 `CI receipt failure-smoke plan check=True`。
- `解释/release-bundle-carryover/`
  - release bundle JSON/Markdown/HTML，显示 `ci_workflow_promoted_seed_receipt_contract_failure_smoke_plan_check_ready=True`。
- `解释/release-readiness-carryover/`
  - readiness JSON/Markdown/HTML，显示 `Readiness status=ready`、`decision=ship`，以及 receipt plan-check ready。
- `解释/source-inputs/`
  - 保留本版复现实验输入，包含 registry、model card、benchmark history、CI workflow hygiene、coverage、gate 和 maturity JSON。
  - 这些输入是为了让 v461 证据能重新运行，不属于需要清理的临时测试缓存。
- `解释/playwright_receipt_plan_carryover_snapshot.md`
  - Playwright MCP 可访问性快照，确认页面上有 `CI receipt plan` 和 `receipt_failure_smoke_plan_check_ready=True`。
- `图片/01-receipt-plan-carryover-readiness.png`
  - Playwright MCP 截图，确认 HTML 页面正常渲染。

## 一句话总结

v461 把 v460 的 CI receipt plan-check 结果从“CI hygiene 内部字段”推进成“发布审计、发布包和 readiness 页面都能直接读取的证据字段”。
