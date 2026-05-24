# v423 promoted training scale decision suite-design carryover 代码讲解

## 本版目标与边界

v423 的目标是把 v422 promoted comparison 已经识别出的 suite-design regression context 带入 promoted baseline decision。promoted decision 是下一轮 baseline/seed 选择前的最终决策层，如果这里只保留 clean-batch 和 CI-regression 原因，就会让带有 benchmark-suite blocker 的 rejected promoted input 在最终报告里失去解释力。

本版不新增训练能力，不改 comparison 生成逻辑，不新增新治理报告。它只读取 promoted comparison 已有字段，并让 decision 层在候选筛选、summary、CSV、Markdown、HTML、CLI 和 recommendation 中继续保留 suite-design regression evidence。

## 前置链路

本版接在 v417-v422 后面：

- v417：training portfolio comparison 产生 suite-design blocker。
- v418-v419：training-scale decision/workflow/handoff 继续携带 suite-design regression。
- v420：promotion acceptance 能因 suite-design regression 阻止 strict clean-batch promotion。
- v421：promotion index 聚合 suite-design regression，并从 compare inputs 排除 dirty clean-required promotions。
- v422：promoted comparison 继续复核这些字段，防止 stale index 漏过滤。
- v423：promoted decision 消费 comparison 输出，确保最终 baseline 选择仍能解释被排除输入。

## 关键文件

### `src/minigpt/promoted_training_scale_decision.py`

`_promotion_rows()` 新增读取 promoted comparison row 中的四个 suite-design 字段：

```text
handoff_batch_maturity_suite_design_regression_count
handoff_batch_maturity_suite_design_regression_names
handoff_selected_batch_maturity_suite_design_regression_count
handoff_selected_batch_maturity_suite_design_regression_names
```

`_rejection_reasons()` 新增 clean-required suite-design 拒绝原因：

```text
handoff batch suite-design regression count is N
```

这和已有 CI regression 原因保持同一层级。即使 comparison row 已经带有 `comparison_exclusion_reasons`，decision 层也会把关键原因写进 rejected candidate 的 `reasons`，方便最终基线审查。

### `src/minigpt/promoted_training_scale_decision_review.py`

`build_decision_handoff_review_summary()` 是本版的汇总中心。它新增三类字段：

- selected baseline：记录被选中 baseline 的 suite-design count 和 names，正常 clean 选择应为 0/空。
- all promotions：聚合所有 promoted inputs 的 suite-design regression count、selected total 和 names。
- comparison-ready subset：只聚合 `promoted_for_comparison=True` 的 suite-design regression 状态，用来证明 dirty evidence 没有进入最终候选池。

clean/unclean 统计也同步把 suite-design regression 纳入判断：

```text
clean status == clean
and ci regression count == 0
and suite-design regression count == 0
```

`append_decision_handoff_clean_batch_recommendations()` 新增 suite-design recommendation：如果 comparison-ready 子集仍有 suite-design regression，则保持 review；如果只有 rejected inputs 有 suite-design regression，则说明这些输入应继续留在 baseline selection 之外。

### `src/minigpt/promoted_training_scale_decision_artifacts.py`

CSV、Markdown 和 HTML 新增 selected/global/comparison-ready suite-design 字段。HTML stat cards 能同时看到：

```text
Selected suite-design regressions = 0
Handoff suite-design regressions = 2
Ready suite-design regressions = 0
```

这三个数字合在一起说明：被选 baseline 是 clean 的，系统仍保留 rejected dirty evidence，并且 dirty evidence 没有进入 comparison-ready 子集。

### `scripts/decide_promoted_training_scale_baseline.py`

CLI stdout 新增 suite-design key/value 输出，包括 selected、global 和 comparison-ready 维度。这样 CI 或命令行审查不用打开 HTML，也能直接看到基线选择是否依赖了 suite-design-regressed evidence。

### `tests/test_promoted_training_scale_decision.py`

新增 `test_carries_promoted_comparison_suite_design_exclusions_into_decision_outputs_and_script()`。测试构造三个 promoted inputs：

- `alpha`：可比较输入。
- `beta`：最终选中的 clean baseline。
- `dirty-suite`：clean-required 但带 suite-design regression，因此被 comparison 排除、decision 拒绝。

测试断言覆盖：

- selected baseline 的 suite-design count 为 0。
- rejected `dirty-suite` 保留 suite-design count、names 和 rejection reason。
- summary 全量 count 为 2，comparison-ready count 为 0。
- CSV、Markdown、HTML 和 CLI 都暴露 suite-design 字段。
- recommendations 解释 rejected promoted inputs 仍带 suite-design regression。

## 核心数据流

```text
promoted_training_scale_comparison.promotions[]
  -> promoted_training_scale_decision._promotion_rows
  -> _rejection_reasons
  -> build_decision_handoff_review_summary
  -> selected_baseline / rejected_runs / summary
  -> JSON / CSV / Markdown / HTML / CLI evidence
```

这个链路没有把 suite-design blocker 当成模型质量提升证据；它只证明 baseline selection 没有依赖带 blocker 的 promoted input。

## 测试覆盖

本轮定向验证：

- `python -m pytest tests\test_promoted_training_scale_decision.py -q`：`10 passed`
- 语法编译：通过

收口验证：

- `python -m pytest -q`：`716 passed`
- `python -B scripts\check_source_encoding.py --out-dir runs\source-encoding-hygiene-v423`：`status=pass`
- `git diff --check`：通过

## 运行证据

`d/423` 归档了本版截图和说明：

- `d/423/图片/01-promoted-training-scale-decision-suite-design.png`
- `d/423/解释/v423-promoted-training-scale-decision-suite-design.html`
- `d/423/解释/v423-promoted-training-scale-decision-suite-design.json`
- `d/423/解释/v423-promoted-training-scale-decision-suite-design-snapshot.md`
- `d/423/解释/说明.md`

一句话总结：v423 把 suite-design blocker 从 promoted comparison 继续带到 promoted baseline decision，使最终基线选择能同时证明“选了谁”和“哪些 dirty promoted inputs 为什么不能选”。
