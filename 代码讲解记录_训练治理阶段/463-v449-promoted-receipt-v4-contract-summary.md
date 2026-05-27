# v449 promoted receipt v4 contract summary

## 本版目标和边界

v448 已经把 promoted training scale clean-batch 的 CI boundary plan-check regression count 写入 automation receipt schema-v4，并通过 receipt check、embedded receipt check 和 handoff assurance 复核。v449 做的是下一层收口：让 receipt contract summary 也能直接表达 schema-v4 readiness 和 boundary plan-check scope。

本版不新增训练能力，不改变 promoted seed handoff 的执行逻辑，不改变 receipt schema-v4 字段名，也不把 boundary plan-check count 解释成模型质量问题。它只解决 contract summary 还停留在 schema-v3 suite-design 视角的问题。

## 前置链路

本版承接三段已有能力：

- v313-v314：promoted seed handoff automation receipt、embedded receipt check 和 assurance sidecar。
- v448：receipt schema 升到 `4`，并携带 boundary plan-check count。
- receipt contract summary：已经能把 schema-v3 suite-design name contract 摊平成 summary、Markdown、HTML 和 summary-check。

v449 在原 contract summary 上补 schema-v4 字段和 v4 scope 表，不新建独立治理链。

## 关键文件

- `src/minigpt/promoted_training_scale_seed_handoff_receipt_contract.py`
  - 新增 `schema_v4_ready`。
  - 新增 `ci_boundary_plan_check_scopes`，包含 selected、handoff、comparison_ready 三个 scope。
  - Text、Markdown、HTML 输出新增 CI boundary plan-check scope 表。
  - Contract issues 新增 schema-v4 readiness 检查和 selected count 不超过 handoff count 的约束。
- `src/minigpt/promoted_training_scale_seed_handoff_receipt_contract_check.py`
  - Summary compare keys 增加 `schema_v4_ready` 和 `ci_boundary_plan_check_scopes`。
  - 如果 contract summary 的 v4 scope 被篡改，summary-check 会从 source handoff 重建 expected summary 并报错。
- `src/minigpt/promoted_training_scale_seed_handoff_assurance_smoke_contract.py`
  - Assurance smoke checks 增加 receipt contract schema-v4 readiness。
  - Smoke output 展示 handoff boundary plan-check handoff/selected count。
- `scripts/check_promoted_seed_handoff_receipt_contract.py`
  - CLI 描述从 schema-v3 contract readiness 改为通用 receipt contract readiness。
- `tests/test_promoted_training_scale_seed_handoff_receipt_contract.py`
  - 覆盖 schema-v4 boundary plan-check scopes 的 summary/text/Markdown/HTML 输出。
- `tests/test_promoted_training_scale_seed_handoff_receipt_contract_check.py`
  - 覆盖 summary-check 对 tampered boundary scope 的拒绝。
- `tests/test_promoted_training_scale_seed_handoff_receipt.py`
  - 覆盖 assurance smoke 输出新增的 schema-v4 contract 字段。

## 核心数据结构

`ci_boundary_plan_check_scopes` 是本版核心结构：

```json
[
  {
    "scope": "handoff",
    "handoff_count": 1,
    "selected_count": 1,
    "selected_within_handoff": true
  }
]
```

字段语义：

- `scope`
  - 当前计数所属范围，固定为 selected、handoff 或 comparison_ready。
- `handoff_count`
  - 该 scope 中 handoff batch maturity CI boundary plan-check readiness regression count。
- `selected_count`
  - 该 scope 中 selected batch maturity 对应的 boundary plan-check readiness regression count。
- `selected_within_handoff`
  - 基本一致性约束，要求 selected count 不超过 handoff count。

这不是新的模型指标，而是 receipt v4 clean-batch 风险字段的 contract summary 表达。

## 运行流程

1. Contract summary 调用 handoff assurance，读取 embedded receipt check 中的 receipt schema 和 v4 boundary 字段。
2. `_ci_boundary_plan_check_scopes()` 把长字段名转换成三个 scope row。
3. Text、Markdown、HTML 渲染同一份 scope row。
4. Contract summary check 读取已生成的 summary，再从原 handoff report 重建 expected summary。
5. 如果 JSON、Markdown、HTML 或 text sidecar 与 expected 不一致，summary-check 返回 fail。
6. Assurance smoke 把 receipt contract schema-v4 readiness 和 boundary count 写入 smoke checks。

## 测试覆盖

Focused tests 共 `37 passed`：

- `tests/test_promoted_training_scale_seed_handoff_receipt_contract.py`
  - 验证 schema-v4 ready、boundary plan-check scopes、text/Markdown/HTML 输出。
- `tests/test_promoted_training_scale_seed_handoff_receipt_contract_check.py`
  - 验证篡改 `ci_boundary_plan_check_scopes` 会被 summary-check 拒绝。
- `tests/test_promoted_training_scale_seed_handoff_receipt.py`
  - 验证 assurance smoke summary 和 stdout 都输出 `receipt_contract_schema_v4_ready=True`。

最终收口验证：

- `python -m pytest tests -q -o cache_dir=runs/pytest-cache-v449`
  - `783 passed`。
- `python -B scripts/check_source_encoding.py --out-dir runs/source-encoding-hygiene-local`
  - `status=pass`，`source_count=351`，`syntax_error_count=0`。
- `git diff --check`
  - 通过；只出现 Git 在 Windows 下的 LF/CRLF 工作区换行提示。

## 运行证据

`d/449` 保存了本版证据：

- `contract-summary/`：基于 `d/448/解释/promoted-handoff` 生成的新 contract summary。
- `contract-summary-check/`：重建 expected summary 后的 sidecar 一致性检查。
- `assurance-smoke/`：端到端 smoke 输出，包含 receipt contract schema-v4 readiness。
- `图片/01-receipt-contract-v4-boundary-summary.png`：Playwright MCP 截图，证明 HTML 中展示 v4 boundary scope 表。
- `解释/playwright_contract_summary_snapshot.md`：Playwright MCP 可访问性快照。

## 一句话总结

v449 让 promoted seed handoff receipt schema-v4 的 boundary plan-check 字段进入 contract summary 和 smoke contract 层，补上了 v448 之后的上层复核入口。
