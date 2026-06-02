# v772 objective-level contrast seed stability rollup 代码讲解

## 本版目标和边界

v772 的目标是把 objective-level contrast 的 seed stability 证据收束成一个可复核 rollup。前面已经有三份 replay-ready 输入：v764 seed `3636`、v769 seed `3737`、v771 seed `3838`。v772 不再跑训练或 replay，而是判断这些 replay 是否满足 v767 plan 中的接受规则。

本版不直接 promotion。输出里明确 `promotion_allowed=False`，只给出 `acceptance_review_ready=True`。

## 前置路线

- v767：生成 seed stability plan，要求 source seed `3636` 加两个补充 seed `3737`、`3838`。
- v768/v769：训练并 replay seed `3737`。
- v770/v771：训练并 replay seed `3838`。
- v772：roll up 三 seed replay 结果。

## 关键新增文件

- `src/minigpt/model_capability_required_term_pair_readiness_objective_level_contrast_seed_stability_rollup.py`
  - rollup 核心逻辑。
  - 输入 seed stability plan 和多个 `seed=path` replay report。
  - 校验 plan 是否通过、seed 是否齐全、是否有非计划 seed、ready replay 数是否达标、是否存在 zero pair-full。
  - 输出 `acceptance_review_ready=True` 和 pair-full count 分布。

- `src/minigpt/model_capability_required_term_pair_readiness_objective_level_contrast_seed_stability_rollup_artifacts.py`
  - 输出 JSON、CSV、TXT、Markdown 和 HTML。
  - HTML 展示 seed rows、checks、pair counts 和 next action。

- `scripts/run_model_capability_required_term_pair_readiness_objective_level_contrast_seed_stability_rollup.py`
  - CLI 入口。
  - 使用 `--plan` 输入 v767 plan。
  - 使用多个 `--replay seed=path` 输入 replay reports。

- `tests/test_model_capability_required_term_pair_readiness_objective_level_contrast_seed_stability_rollup.py`
  - 覆盖三 seed ready、缺少 seed 失败、replay 不 ready 失败、locator 和 artifact 输出。

## 核心数据结构

每个 seed 会被归一化为一行：

```text
seed
source_path
status
decision
exact_heldout_pair_full
required_all_pair_full
pair_full_count
pair_full_rate
ready
```

`ready` 同时要求：

- replay report `status=pass`
- decision 为 `pair_readiness_fixed_preserving_transfer_pair_probe_replay_ready`
- `exact_heldout_pair_full=True`
- `required_all_pair_full=True`
- `pair_full_count>0`

## 检查逻辑

v772 的 checks 包括：

- seed stability plan 必须 pass。
- plan decision 必须是 `pair_readiness_objective_level_contrast_seed_stability_plan_ready`。
- 三个计划 seed 必须全部出现。
- 不能混入非计划 seed。
- ready replay 数必须达到 plan 中的 `minimum_ready_replay_count`。
- 不能有 seed 退化到零 pair-full。
- 每个 observed replay 都必须 ready。

这些检查让 rollup 不只是计数器，而是一个可作为后续 acceptance review 输入的 contract。

## 真实输入输出

真实输入：

```text
plan: e/767/解释/model-capability-required-term-pair-readiness-objective-level-contrast-seed-stability-plan
3636: e/764/解释/model-capability-required-term-pair-readiness-objective-level-contrast-pair-probe-replay
3737: e/769/解释/model-capability-required-term-pair-readiness-objective-level-contrast-seed-3737-pair-probe-replay
3838: e/771/解释/model-capability-required-term-pair-readiness-objective-level-contrast-seed-3838-pair-probe-replay
```

真实输出：

```text
e/772/解释/model-capability-required-term-pair-readiness-objective-level-contrast-seed-stability-rollup
```

核心结论：

```text
status=pass
decision=pair_readiness_objective_level_contrast_seed_stability_ready_for_acceptance_review
acceptance_review_ready=True
promotion_allowed=False
observed_seed_count=3
ready_replay_count=3
pair_full_counts={'3636': 3, '3737': 2, '3838': 2}
uniform_pair_full_strength=False
```

`uniform_pair_full_strength=False` 很重要：它说明三 seed 都过了 replay gate，但强度并不完全一致，后续 acceptance review 应该继续保留这个事实。

## 测试覆盖

Focused tests 覆盖：

- 三个计划 seed 都 ready 时，rollup 通过并进入 acceptance review。
- 缺少计划 seed 时失败。
- 任一 replay 退化到 zero pair-full 或不 ready 时失败。
- locator、文本、Markdown、HTML、CSV/JSON 输出可用。

这组测试保护的是 seed-stability rollup 的 contract 边界，而不是训练数值本身。

## 运行证据

真实运行命令：

```powershell
python -B scripts\run_model_capability_required_term_pair_readiness_objective_level_contrast_seed_stability_rollup.py --plan e\767\解释\model-capability-required-term-pair-readiness-objective-level-contrast-seed-stability-plan --replay 3636=e\764\解释\model-capability-required-term-pair-readiness-objective-level-contrast-pair-probe-replay --replay 3737=e\769\解释\model-capability-required-term-pair-readiness-objective-level-contrast-seed-3737-pair-probe-replay --replay 3838=e\771\解释\model-capability-required-term-pair-readiness-objective-level-contrast-seed-3838-pair-probe-replay --out-dir e\772\解释\model-capability-required-term-pair-readiness-objective-level-contrast-seed-stability-rollup --require-pass --force
```

Playwright 截图位于：

```text
e/772/图片/v772-objective-level-contrast-seed-stability-rollup.png
```

一句话总结：v772 把 objective-level contrast 的三 seed replay 证据收束成 acceptance-review-ready 候选，但仍保留最终 promotion gate。
