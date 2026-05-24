# v424 promoted training scale seed suite-design carryover 代码讲解

## 本版目标与边界

v424 的目标是把 v423 promoted baseline decision 中的 suite-design regression context 继续带入 promoted training scale next-cycle seed。seed 是下一轮 `plan_training_scale.py` 命令的交接产物，如果它只记录 selected baseline 而不记录 rejected evidence 的 suite-design 风险，后续计划就缺少“为什么某些 promoted inputs 没有进入下一轮”的上下文。

本版不执行训练，不改 baseline selection，不新增新的治理链。它只读取 decision summary 已有字段，写入 seed 的 `handoff_clean_batch_review`、summary、CSV、Markdown、HTML、CLI 和 recommendations。

## 前置链路

本版接在 v417-v423 后面：

- v417：training portfolio comparison 产生 suite-design blocker。
- v418-v421：training-scale decision、handoff、promotion、promotion index 持续携带并过滤 suite-design regression。
- v422：promoted comparison 复核 suite-design regression，防止 stale index 漏过滤。
- v423：promoted decision 在 rejected candidates 和 summary 中保留 suite-design 拒绝原因。
- v424：promoted seed 消费这些字段，让下一轮计划种子也保留该解释。

## 关键文件

### `src/minigpt/promoted_training_scale_seed_review.py`

`build_seed_handoff_clean_batch_review()` 新增读取 selected/global/comparison-ready 三层 suite-design 字段：

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

`build_seed_handoff_clean_batch_review_summary()` 把这些字段提升到 seed summary，供 artifact writers 和 CLI 统一消费。

`append_seed_handoff_clean_batch_recommendation()` 新增 suite-design recommendation：如果 selected baseline 自身带 suite-design regression，就要求先修复；如果只有 rejected decision inputs 带 suite-design regression，则说明这些输入不能进入 next-cycle seed baseline。

### `src/minigpt/promoted_training_scale_seed_artifacts.py`

CSV 字段、Markdown summary 和文本输出新增 suite-design 信息。关键语义是：

```text
selected suite-design = 0
global suite-design = 2
comparison-ready suite-design = 0
```

这说明 seed baseline 本身 clean，同时 rejected evidence 的风险没有丢。

### `src/minigpt/promoted_training_scale_seed_sections.py`

HTML stat cards 和 Baseline Seed 明细表新增 suite-design 字段。截图里可以直接看到 selected/global/ready 三层数值，不需要打开 JSON。

### `scripts/build_promoted_training_scale_seed.py`

CLI stdout 新增 suite-design key/value 输出，包括 selected、global 和 comparison-ready 维度。这样 CI 或 shell-only 审查可以直接读取：

```text
handoff_batch_maturity_suite_design_regression_count=2
comparison_ready_handoff_batch_maturity_suite_design_regression_count=0
```

### `tests/test_promoted_training_scale_seed.py`

新增 `test_carries_decision_suite_design_exclusions_into_seed_outputs_and_script()`。测试构造一个 accepted decision：

- selected baseline `beta` 的 suite-design regression count 为 0。
- decision summary 中保留 rejected input 的 suite-design regression count 为 2。
- comparison-ready suite-design regression count 为 0。

测试断言覆盖 JSON summary、seed review payload、CSV、Markdown、HTML、CLI stdout 和 recommendations。

## 核心数据流

```text
promoted_training_scale_decision.summary
  -> build_seed_handoff_clean_batch_review
  -> baseline_seed.handoff_clean_batch_review
  -> build_seed_handoff_clean_batch_review_summary
  -> seed summary
  -> JSON / CSV / Markdown / HTML / CLI evidence
```

这个链路不证明模型能力提升；它证明 next-cycle seed 没有把 suite-design-regressed promoted evidence 当作 clean baseline。

## 测试覆盖

本轮定向验证：

- `python -m pytest tests\test_promoted_training_scale_seed.py -q`：`13 passed`
- 语法编译：通过

收口验证：

- `python -m pytest -q`：`717 passed`
- `python -B scripts\check_source_encoding.py --out-dir runs\source-encoding-hygiene-v424`：`status=pass`
- `git diff --check`：通过

## 运行证据

`d/424` 归档了本版截图和说明：

- `d/424/图片/01-promoted-training-scale-seed-suite-design.png`
- `d/424/解释/v424-promoted-training-scale-seed-suite-design.html`
- `d/424/解释/v424-promoted-training-scale-seed-suite-design.json`
- `d/424/解释/v424-promoted-training-scale-seed-suite-design-snapshot.md`
- `d/424/解释/说明.md`

一句话总结：v424 把 suite-design blocker 从 promoted decision 继续带到 next-cycle seed，让后续训练计划既能继承 clean baseline，也能保留 rejected dirty evidence 的边界说明。
