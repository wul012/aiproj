# v448 promoted boundary plan clean-batch carryover

## 本版目标和边界

v447 已经把 release-readiness 层的 CI boundary plan-check regression 推到 maturity 和 training portfolio review。v448 做同一类收口，但位置换到 promoted training scale 主线：从 comparison 开始，把 handoff clean-batch 中的 boundary plan-check regression count 继续传到 promoted decision、next-cycle seed、seed handoff、automation receipt、embedded receipt check 和 assurance。

本版不新增新治理链，不重新训练模型，不改变 promoted baseline 的选择算法，也不把 `boundary_gate_plan_check_not_ready` 解释成模型生成质量问题。它解决的是 clean-batch 证据的可复核性：下游不应该只看到泛化的 CI regression count，还要能看到其中有多少是 boundary plan-check readiness regression。

## 前置链路

本版承接 v433-v447 的几条能力：

- promoted comparison/decision/seed/handoff 已经能传递 handoff batch CI regression 和 suite-design regression。
- v444-v447 已经把 boundary plan-check readiness regression 定义成稳定 reason：`boundary_gate_plan_check_not_ready`。
- v313-v314 已经有 promoted seed handoff automation receipt、embedded receipt check 和 assurance sidecar。

v448 在这些既有链路上补字段，不改变原有输出文件名和默认 CLI 行为。

## 关键文件

- `src/minigpt/report_utils.py`
  - 新增 `CI_BOUNDARY_PLAN_CHECK_READY_REGRESSION_REASON`。
  - 新增 `ci_boundary_plan_check_ready_regression_count()`，优先读取显式 count；没有显式 count 时，从 reason map 中解析 `boundary_gate_plan_check_not_ready`。
- `src/minigpt/promoted_training_scale_comparison.py`
  - `_clean_batch_review_guard()` 从 row、guard、summary 和 reason map 中推导 boundary plan-check count。
  - Promotion row 和 summary 同时输出 handoff total、selected total、comparison-ready total。
- `src/minigpt/promoted_training_scale_comparison_artifacts.py`
  - CSV、Markdown、HTML 都展示 boundary plan-check count。
- `src/minigpt/promoted_training_scale_decision.py`
  - Rejected run 和 selected baseline row 保留 boundary plan-check count。
- `src/minigpt/promoted_training_scale_decision_review.py`
  - Decision summary 增加 selected/rejected/comparison-ready boundary plan-check 字段。
  - Recommendation 把该问题解释成 “handoff batch CI regressions caused by boundary plan-check readiness”，既保留泛化 CI 检索词，又明确具体原因。
- `src/minigpt/promoted_training_scale_decision_artifacts.py`
  - Decision 的 CSV、Markdown、HTML 输出同步展示这些字段。
- `src/minigpt/promoted_training_scale_seed_review.py`
  - Seed clean-batch review 从 decision summary 继续接收 boundary plan-check count。
  - Selected handoff 如果携带 boundary plan-check regression，会优先给出边界检查相关建议。
- `src/minigpt/promoted_training_scale_seed_artifacts.py`
  - Seed JSON/CSV/Markdown/HTML/CLI 输出保留 boundary plan-check 字段。
- `src/minigpt/promoted_training_scale_seed_handoff_review.py`
  - Handoff clean-batch requirement 新增 `selected_ci_boundary_plan_check_ready_regression_count`。
  - Strict clean-batch requirement 把 selected boundary plan-check regression 视为 dirty evidence。
- `src/minigpt/promoted_training_scale_seed_handoff_artifacts.py`
  - Handoff CSV 输出新增 selected、total、comparison-ready boundary plan-check 字段。
- `src/minigpt/promoted_training_scale_seed_handoff_sections.py`
  - Handoff Markdown/HTML summary 展示 boundary count、requirement count、receipt assurance count。
- `src/minigpt/promoted_training_scale_seed_handoff_receipt_artifacts.py`
  - Automation receipt schema 升到 `4`。
  - Receipt JSON/text 写入 selected、handoff total、comparison-ready boundary plan-check 字段。
- `src/minigpt/promoted_training_scale_seed_handoff_receipt.py`
  - Receipt check 增加 schema v4 required fields。
  - Embedded receipt check 比对 v4 boundary 字段，防止主报告和 sidecar 不一致。
- `src/minigpt/promoted_training_scale_seed_handoff_assurance.py`
  - Assurance 复核 embedded receipt check 中的 v4 boundary 字段。
- `scripts/compare_promoted_training_scale_runs.py`
- `scripts/decide_promoted_training_scale_baseline.py`
- `scripts/build_promoted_training_scale_seed.py`
- `scripts/execute_promoted_training_scale_seed.py`
  - CLI stdout 都打印 boundary plan-check count，方便 CI 日志和人工 shell 检查。

## 核心字段

本版围绕 6 个下游字段：

- `selected_handoff_batch_maturity_ci_boundary_plan_check_ready_regression_count`
- `selected_handoff_selected_batch_maturity_ci_boundary_plan_check_ready_regression_count`
- `handoff_batch_maturity_ci_boundary_plan_check_ready_regression_count`
- `handoff_selected_batch_maturity_ci_boundary_plan_check_ready_regression_total`
- `comparison_ready_handoff_batch_maturity_ci_boundary_plan_check_ready_regression_count`
- `comparison_ready_handoff_selected_batch_maturity_ci_boundary_plan_check_ready_regression_total`

这些字段的语义很窄：它们表示 handoff clean-batch CI regression 中有多少来自 boundary plan-check readiness，不表示模型质量下降，也不表示训练失败。

## 运行流程

1. Promotion index row 或 clean-batch guard 携带 `handoff_batch_maturity_ci_regression_reason_counts`。
2. Comparison 层用 `ci_boundary_plan_check_ready_regression_count()` 从显式字段或 reason map 中提取 count。
3. Decision 层把 rejected promoted input 的 count 放进 summary 和 rejected row。
4. Seed 层继续保留 rejected input count，同时保持 selected baseline 的 clean count 为 0。
5. Handoff 层把 count 写入 summary、Markdown、HTML、CSV 和 automation receipt。
6. Receipt check、embedded receipt check、handoff assurance 重新读取同一批字段并比较，形成 sidecar 级复核。

## 测试覆盖

本版先用 focused tests 覆盖 5 个主链路测试文件，共 `69 passed`：

- `tests/test_promoted_training_scale_comparison.py`
  - 证明 comparison row、summary、CSV、Markdown、HTML、CLI 都带 boundary plan-check count。
- `tests/test_promoted_training_scale_decision.py`
  - 证明 rejected promoted input 和 decision summary 保留 boundary plan-check count 与 reason map。
- `tests/test_promoted_training_scale_seed.py`
  - 证明 seed clean-batch review 继续携带 rejected input 的 boundary plan-check count。
- `tests/test_promoted_training_scale_seed_handoff.py`
  - 证明 handoff summary、CSV、Markdown、HTML、CLI、automation receipt 都保留 v4 字段。
  - 证明 strict clean-batch gate 会把 selected boundary plan-check regression 视为 dirty。
- `tests/test_promoted_training_scale_seed_handoff_review.py`
  - 证明 clean-batch requirement detail 优先解释 boundary plan-check regression。

随后补跑 receipt/schema v4 相关测试，确认当前 builder 输出的 receipt schema 从 v3 升到 v4 后，contract summary、assurance smoke 和 suite-design sidecar 仍然一致：

- `tests/test_promoted_training_scale_seed_handoff_receipt.py`
- `tests/test_promoted_training_scale_seed_handoff_receipt_contract.py`
- `tests/test_promoted_training_scale_seed_handoff_receipt_contract_check.py`
- `tests/test_promoted_training_scale_seed_handoff_receipt_suite_design.py`

最终收口验证：

- `python -m pytest tests -q -o cache_dir=runs/pytest-cache-v448`
  - `781 passed`。
- `python -B scripts/check_source_encoding.py --out-dir runs/source-encoding-hygiene-local`
  - `status=pass`，`source_count=351`，`syntax_error_count=0`。
- `git diff --check`
  - 通过；只出现 Git 在 Windows 下的 LF/CRLF 工作区换行提示。

## 运行证据

`d/448` 保存了本版证据：

- `fixture/`：受控 promoted training scale fixture，包含一个携带 `boundary_gate_plan_check_not_ready=1` 的 rejected input。
- `promoted-comparison/`：comparison 输出，summary 中 `handoff_batch_maturity_ci_boundary_plan_check_ready_regression_count=1`。
- `promoted-decision/`：decision 输出，selected `gamma` clean，但 rejected input 的 boundary count 保留。
- `promoted-seed/`：seed 输出，review 状态下继续保留 rejected boundary count。
- `promoted-handoff/`：handoff 输出和 automation receipt，receipt schema 为 `4`。
- `receipt-check/`、`embedded-receipt-check/`、`handoff-assurance/`：三层检查均为 `pass`。
- `图片/01-promoted-seed-handoff-boundary-plan.png`：handoff HTML 截图。
- `图片/02-promoted-comparison-boundary-plan.png`：comparison HTML 截图。

## 一句话总结

v448 把 promoted training scale clean-batch 的 boundary plan-check regression 从上游比较层推到 handoff receipt 和 assurance 层，让 seed handoff 自动化可以直接复核这类窄语义 CI 风险。
