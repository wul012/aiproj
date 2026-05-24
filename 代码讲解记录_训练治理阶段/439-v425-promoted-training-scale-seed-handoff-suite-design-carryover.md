# v425 promoted training scale seed handoff suite-design carryover 代码讲解

## 本版目标与边界

v425 的目标是把 v424 promoted training scale next-cycle seed 中的 suite-design regression context 继续带入 promoted seed handoff。seed handoff 是计划执行前的最后一份交接报告，如果它只保留 CI regression 和 clean-batch 状态，不保留 suite-design 被拒原因，后续自动化会知道“可以执行”，但不知道“哪些输入为什么不能作为 clean baseline”。

本版不执行训练，不改变 selected baseline，不升级 automation receipt schema，也不新增治理链。它只读取 seed 中已有的 `baseline_seed.handoff_clean_batch_review` 字段，并把 selected/global/comparison-ready 三层 suite-design 信息写入 handoff summary、clean-batch requirement、CSV、Markdown、HTML、CLI stdout 和 recommendations。

## 前置链路

本版接在 v417-v424 后面：

- v417：training portfolio comparison 产生 suite-design review/blocker。
- v418-v421：training-scale decision、handoff、promotion、promotion index 逐层携带 suite-design regression。
- v422：promoted comparison 复核 clean-required promoted inputs，防止 stale index 漏过滤。
- v423：promoted decision 在 rejected candidates 和 summary 中保留 suite-design 拒绝原因。
- v424：promoted next-cycle seed 消费 decision summary，让 seed 保留 selected clean baseline 和 rejected dirty evidence。
- v425：promoted seed handoff 消费 seed 字段，让最后交接报告不丢 suite-design 解释。

## 关键文件

### `src/minigpt/promoted_training_scale_seed_handoff_review.py`

`build_seed_handoff_clean_batch_review_summary()` 新增读取 12 个 suite-design 字段：

```text
selected_handoff_batch_maturity_suite_design_regression_count
selected_handoff_batch_maturity_suite_design_regression_names
selected_handoff_selected_batch_maturity_suite_design_regression_count
selected_handoff_selected_batch_maturity_suite_design_regression_names
handoff_batch_maturity_suite_design_regression_count
handoff_selected_batch_maturity_suite_design_regression_total
handoff_batch_maturity_suite_design_regression_names
handoff_selected_batch_maturity_suite_design_regression_names
comparison_ready_handoff_batch_maturity_suite_design_regression_count
comparison_ready_handoff_selected_batch_maturity_suite_design_regression_total
comparison_ready_handoff_batch_maturity_suite_design_regression_names
comparison_ready_handoff_selected_batch_maturity_suite_design_regression_names
```

`SeedHandoffCleanBatchReviewRequirement` 新增：

```text
selected_suite_design_regression_count
selected_suite_design_regression_names
```

严格 clean-batch gate 的语义也随之补齐：selected handoff 只要携带 selected suite-design regression，就会被判为 dirty；但 global/rejected suite-design regression 仍然只作为解释上下文，不阻塞 selected clean baseline。

### `src/minigpt/promoted_training_scale_seed_handoff_artifacts.py`

CSV 输出新增 selected/global/comparison-ready suite-design 字段，并把 `clean_batch_review_requirement_selected_suite_design_regression_count` 写入机器可读列。这样 CI 或 shell-only 审查不用打开 JSON，也能看到 gate 为什么 pass 或 fail。

### `src/minigpt/promoted_training_scale_seed_handoff_sections.py`

Markdown 和 HTML stat cards 新增 suite-design 行。截图里可以直接看到：

```text
Selected suite-design regressions = 0
Handoff suite-design regressions = 2
Ready suite-design regressions = 0
Clean batch gate selected suite-design = 0
```

这组数值表达的是：最终 handoff 选中的 baseline 干净，同时 rejected inputs 的 suite-design 风险没有丢。

### `scripts/execute_promoted_training_scale_seed.py`

CLI stdout 新增 selected/global/comparison-ready suite-design key/value 输出，并在 `--require-clean-batch-review` 时打印 selected suite-design gate 诊断：

```text
handoff_batch_maturity_suite_design_regression_count=2
comparison_ready_handoff_batch_maturity_suite_design_regression_count=0
clean_batch_review_required_selected_suite_design_regression_count=0
clean_batch_review_required=pass
```

### `tests/test_promoted_training_scale_seed_handoff_suite_design.py`

没有继续扩充已有 1300 行级别的 seed handoff 测试文件，而是新增聚焦测试文件。测试构造一个 promoted seed fixture：

- selected baseline 没有 suite-design regression。
- handoff global/rejected context 中保留 2 个 suite-design regression 名称。
- comparison-ready context 中 suite-design regression 为 0。
- strict clean-batch handoff gate 通过。

测试覆盖 JSON summary、requirement contract、CSV、Markdown、HTML、CLI stdout 和 recommendations。

## 核心数据流

```text
promoted_training_scale_seed.baseline_seed.handoff_clean_batch_review
  -> build_seed_handoff_clean_batch_review_summary
  -> promoted seed handoff summary
  -> clean_batch_review_requirement
  -> JSON / CSV / Markdown / HTML / CLI evidence
```

这个链路不证明模型能力提升；它证明 final handoff 没有把 suite-design-regressed rejected evidence 当成 selected clean baseline，同时保留了为什么拒绝这些输入的解释。

## 测试覆盖

本轮定向验证：

- `python -m pytest tests\test_promoted_training_scale_seed_handoff_suite_design.py -q`：`1 passed`
- `python -m pytest tests\test_promoted_training_scale_seed_handoff.py tests\test_promoted_training_scale_seed_handoff_receipt.py -q`：`56 passed`
- 语法编译：通过

收口验证：

- `python -m pytest -q`：`718 passed`
- `python -B scripts\check_source_encoding.py --out-dir runs\source-encoding-hygiene-v425`：`status=pass`
- `git diff --check`：通过

## 运行证据

`d/425` 归档了本版截图和说明：

- `d/425/图片/01-promoted-training-scale-seed-handoff-suite-design.png`
- `d/425/解释/v425-promoted-training-scale-seed-handoff-suite-design.html`
- `d/425/解释/v425-promoted-training-scale-seed-handoff-suite-design.json`
- `d/425/解释/v425-promoted-training-scale-seed-handoff-suite-design-snapshot.md`
- `d/425/解释/说明.md`

一句话总结：v425 把 suite-design blocker 从 promoted seed 继续送到 final seed handoff，让自动化最后一跳既能严格放行 selected clean evidence，也能保留 rejected dirty evidence 的解释边界。
