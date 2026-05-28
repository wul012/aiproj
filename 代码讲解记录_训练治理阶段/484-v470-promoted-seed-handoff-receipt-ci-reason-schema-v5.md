# v470：promoted seed handoff receipt schema v5 CI reason contract

## 本版目标与边界

v470 解决的是 promoted seed handoff 最终 receipt contract 的证据粒度问题。

v467-v469 已经证明 `archived_path_portability_check_not_ready` 可以沿通用 `*_ci_regression_reason_counts` 进入 promoted comparison、decision、seed 和最终 handoff。v470 不再增加新的 archived-path 专用字段，而是把这些 reason-count map 放进 automation receipt schema v5，并让 receipt check、embedded check、handoff assurance、contract summary 和 summary-check 都能复核它们。

本版不改变模型训练逻辑，不改变 baseline/candidate 选择策略，也不扩大治理链。它只升级最终交接产物的契约表达和验证覆盖。

## 关键新增或修改文件

- `src/minigpt/promoted_training_scale_seed_handoff_receipt_artifacts.py`
  - 将 automation receipt 的 `schema_version` 升为 `5`。
  - 新增 selected、selected-selected、handoff、handoff-selected、comparison-ready、clean-batch requirement 的 CI regression reason-count 字段。
  - 文本输出和 assurance section 也显示这些 map，方便从纯文本证据中定位原因。
- `src/minigpt/promoted_training_scale_seed_handoff_receipt.py`
  - 新增 schema-v5 required field 检查。
  - receipt checker、embedded receipt checker、sidecar 对比和 text renderer 都认识 v5 reason-count 字段。
  - 为旧 schema-v4 sidecar 加了按 schema 过滤 compare keys 的兼容逻辑，避免历史归档因为新字段而误报。
- `src/minigpt/promoted_training_scale_seed_handoff_assurance.py`
  - handoff assurance 继续向上暴露 receipt reason-count map。
  - assurance 对嵌入式 receipt-check JSON/text 的比较也按 schema 过滤 v5 字段。
- `src/minigpt/promoted_training_scale_seed_handoff_receipt_contract.py`
  - contract summary 增加 `schema_v5_ready`。
  - HTML/Markdown/text 都显示 receipt 是否达到 schema v5。
- `src/minigpt/promoted_training_scale_seed_handoff_receipt_contract_rows.py`
  - contract checks 增加 `schema_v5_ready` 行。
  - 这让 schema v5 不只是一个摘要字段，而是 contract check table 里的机器可读检查项。
- `src/minigpt/promoted_training_scale_seed_handoff_receipt_contract_check.py`
  - summary-check 的 rebuild compare keys 加入 `schema_v5_ready`。
  - 如果 contract summary 被篡改为非 v5，summary-check 能显示实际值与重建值不一致。
- `src/minigpt/promoted_training_scale_seed_handoff_sections.py`
  - handoff report 的 Markdown/HTML summary 增加 selected、aggregate、ready 三层 CI reason map。
- `scripts/check_promoted_seed_handoff_assurance_smoke.py`
  - smoke gate 现在要求新生成的 handoff assurance 暴露 receipt schema version `5`。

## 核心数据结构

schema v5 的新增字段集中在 automation receipt：

```text
clean_batch_review_requirement_selected_ci_regression_reason_counts
selected_handoff_batch_maturity_ci_regression_reason_counts
selected_handoff_selected_batch_maturity_ci_regression_reason_counts
handoff_batch_maturity_ci_regression_reason_counts
handoff_selected_batch_maturity_ci_regression_reason_counts
comparison_ready_handoff_batch_maturity_ci_regression_reason_counts
comparison_ready_handoff_selected_batch_maturity_ci_regression_reason_counts
```

这些字段的值都是 `{reason: count}` map。v470 复用 `report_utils.positive_int_mapping()` 做规范化，确保读取时只保留正整数原因计数，避免字符串、空原因或负数进入 contract。

## 运行流程

本版最终链路是：

```text
promoted seed
  -> seed handoff report
  -> automation receipt schema v5
  -> receipt check
  -> embedded receipt check
  -> handoff assurance
  -> receipt contract summary
  -> receipt contract summary check
```

receipt check 负责校验单个 receipt 的结构和字段语义。embedded receipt check 负责确认主 handoff JSON 内嵌的 receipt-check 与 sidecar 文件一致。handoff assurance 负责从目录层重新复核完整 handoff。contract summary 再把 assurance 中的 schema readiness、suite-design 一致性、CI boundary plan-check 一致性整理成可读 contract table。

## 兼容性处理

v470 的一个关键边界是旧归档不应该被新 schema 误伤。

旧 v448 归档中的 receipt-check sidecar 是 schema v4，它没有 v5 reason-count 行。v470 因此增加了按 schema 过滤的比较逻辑：当历史 sidecar 标记为 schema v4 时，checker 只比较 v4 应该具备的字段；新生成的 v470 sidecar 则必须通过 `schema_v5_ready=True`。

这让“历史证据可读”和“新证据更严格”同时成立。

## 测试覆盖

本版测试重点覆盖三类风险：

- schema v5 字段缺失或类型错误会被 receipt checker 报错。
- generated receipt、embedded check、assurance 和 smoke contract 都要求新产物显示 schema version `5`。
- archived path portability 和旧 sidecar 相关测试继续通过，证明 schema v4 历史归档不会被 v5 字段误判。

关键验证命令包括：

```text
python -m pytest tests/test_promoted_training_scale_seed_handoff.py tests/test_promoted_training_scale_seed_handoff_receipt.py tests/test_promoted_training_scale_seed_handoff_receipt_contract.py tests/test_promoted_training_scale_seed_handoff_review.py -q -o cache_dir=runs/pytest-cache-v470-target
python -m pytest tests/test_promoted_training_scale_seed_handoff_receipt_contract_check.py tests/test_ci_promoted_seed_receipt_contract_failure_smoke.py tests/test_archived_path_portability.py -q -o cache_dir=runs/pytest-cache-v470-contract
```

## 运行证据

证据目录：`d/470`

主要文件：

- `d/470/解释/promoted-seed-handoff/promoted_training_scale_seed_handoff_automation_receipt.json`
- `d/470/解释/receipt-check/promoted_training_scale_seed_handoff_automation_receipt_check.json`
- `d/470/解释/embedded-receipt-check/promoted_training_scale_seed_handoff_embedded_receipt_check.json`
- `d/470/解释/handoff-assurance/promoted_training_scale_seed_handoff_assurance.json`
- `d/470/解释/contract-summary/promoted_training_scale_seed_handoff_receipt_contract_summary.json`
- `d/470/解释/contract-summary-check/promoted_training_scale_seed_handoff_receipt_contract_summary_check.json`
- `d/470/图片/01-contract-summary-schema-v5.png`
- `d/470/图片/02-contract-summary-check-pass.png`

这些证据显示 contract summary `status=pass`、`schema_v5_ready=True`、summary-check `failed_summary_field_check_count=0`、`failed_contract_profile_check_count=0`、`failed_sidecar_check_count=0`。

## 一句话总结

v470 把 promoted seed handoff 的 CI regression reason-count 从最终报告字段提升为 receipt schema-v5 契约字段，使自动化交接不只知道“有回归”，还可以复核“是什么原因造成的回归”。
