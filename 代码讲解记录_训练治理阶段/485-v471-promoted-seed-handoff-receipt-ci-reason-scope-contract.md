# v471：promoted seed handoff receipt CI reason-count scope contract

## 本版目标与边界

v471 的目标是补齐 v470 后留下的一个自然缺口：receipt schema v5 已经能保存 CI regression reason-count map，但 contract summary 还没有显式检查 selected reason map 是否被 handoff aggregate reason map 覆盖。

本版新增的是 contract-level 检查，不改变 promoted seed handoff 的生成、执行、自动化 gate 和训练流程。它不新增 archived-path 专用字段，也不引入新的治理链；所有检查都建立在 v470 已有的通用 reason-count map 上。

## 关键修改文件

- `src/minigpt/promoted_training_scale_seed_handoff_receipt_contract_context.py`
  - 新增 `ci_reason_count_scopes()` 和 `ci_reason_count_scope()`。
  - 每个 scope 记录 handoff reason map、selected reason map、总数、缺失原因、超额原因以及 `selected_reasons_within_handoff`。
  - `contract_issues()` 增加 reason scope 检查，selected reason 超出 handoff 时输出明确 issue。
- `src/minigpt/promoted_training_scale_seed_handoff_receipt_contract_rows.py`
  - `build_contract_checks()` 增加三条 `reason_counts_within_handoff` contract check。
  - 三个 scope 分别是 `selected`、`handoff`、`comparison_ready`。
- `src/minigpt/promoted_training_scale_seed_handoff_receipt_contract.py`
  - contract summary 新增 `ci_reason_count_scopes`。
  - text、Markdown、HTML 都新增 CI Reason-Count Scopes 输出区。
- `src/minigpt/promoted_training_scale_seed_handoff_receipt_contract_check.py`
  - summary-check 对比键加入 `ci_reason_count_scopes`，防止 summary JSON 中的 reason scope 被篡改。
- `src/minigpt/promoted_training_scale_seed_handoff_assurance_smoke_contract.py`
  - smoke contract 增加 handoff scope reason-count selected-within-handoff 检查。
- `tests/test_promoted_training_scale_seed_handoff_receipt_contract.py`
  - 覆盖 pass 场景和 fail 场景。
  - fail 场景中 selected reason 为 `missing-ci-step`，但 handoff aggregate reason map 只有 `workflow-order-regressed`，因此 contract summary 必须失败。

## 核心数据结构

`ci_reason_count_scopes` 的每一行都类似：

```text
scope
handoff_reason_counts
selected_reason_counts
handoff_reason_total
selected_reason_total
missing_reasons
missing_reason_count
excess_reason_counts
selected_reasons_within_handoff
```

判断规则很直接：对 selected map 中的每个 reason，要求 `selected_count <= handoff_count`。如果 selected 中出现 handoff 没有的 reason，handoff count 等于 0，因此也会被判为不一致。

## 运行流程

```text
handoff assurance
  -> ci_reason_count_scopes
  -> reason_counts_within_handoff contract checks
  -> contract summary
  -> contract summary-check rebuild comparison
  -> smoke contract gate
```

这样，reason-count 不再只是 JSON 字段，而是 contract table 中可统计、可失败、可被 summary-check 复算的检查项。

## 测试覆盖

本版测试新增两类断言：

- 正常场景：selected `archived_path_portability_check_not_ready:1` 被 handoff aggregate 中同名 reason 覆盖，summary pass。
- 异常场景：selected `missing-ci-step:1` 不存在于 handoff aggregate reason map，`ci_reason_counts_handoff_selected_within_handoff` fail，summary issue 指明 handoff selected reasons exceed handoff reasons。

目标测试：

```text
python -m pytest tests/test_promoted_training_scale_seed_handoff_receipt_contract.py tests/test_promoted_training_scale_seed_handoff_receipt_contract_check.py tests/test_promoted_training_scale_seed_handoff_receipt.py -q -o cache_dir=runs/pytest-cache-v471-contract
```

## 运行证据

证据目录：`d/471`

主要文件：

- `d/471/解释/contract-summary/promoted_training_scale_seed_handoff_receipt_contract_summary.json`
- `d/471/解释/contract-summary/promoted_training_scale_seed_handoff_receipt_contract_summary.html`
- `d/471/解释/contract-summary-check/promoted_training_scale_seed_handoff_receipt_contract_summary_check.json`
- `d/471/解释/contract-summary-check/promoted_training_scale_seed_handoff_receipt_contract_summary_check.html`
- `d/471/图片/01-contract-summary-reason-scopes.png`
- `d/471/图片/02-contract-summary-check-reason-scopes.png`

这些证据显示 `reason_counts_within_handoff` 类型的 3 条检查全部 pass，并且 summary-check 能复算 `ci_reason_count_scopes`。

## 一句话总结

v471 把 promoted seed handoff receipt 的 CI reason-count map 从字段携带提升为 contract-level 一致性约束。
