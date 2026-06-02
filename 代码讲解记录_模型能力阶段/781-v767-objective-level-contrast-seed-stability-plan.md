# v767 objective-level contrast seed stability plan 代码讲解

## 本版目标和边界

v767 的目标是承接 v766 promotion guard，生成 objective-level contrast 的 seed stability plan。v766 已经确认 route candidate 足够进入稳定性验证，但不能直接接受；v767 就把这个“需要 seed stability”的结论转成明确的补充 seed、后续 artifact 和接受规则。

本版不训练模型，不 replay pair probes，也不改变 corpus、模型规模或解码参数。它的模型质量声明保持为 `plan_only`。

## 前置路线

- v762：materialize objective-level contrast corpus。
- v763：用 seed `3636` 训练 objective-level contrast checkpoint。
- v764：对 v763 checkpoint 进行 pair-probe replay，观察到三种 pair surface full。
- v765：确认 objective-level contrast route 胜出，但需要 promotion guard。
- v766：promotion guard 通过，同时设置 `promotion_allowed=False` 和 `required_next_artifact=pair_readiness_objective_level_contrast_seed_stability_plan`。
- v767：把 v766 的 required next artifact 落成 seed stability plan。

## 关键新增文件

- `src/minigpt/model_capability_required_term_pair_readiness_objective_level_contrast_seed_stability_plan.py`
  - 核心 plan builder。
  - 输入 v766 promotion guard JSON 或目录。
  - 校验 guard 是否通过、decision 是否匹配、promotion 是否仍被阻止、required next artifact 是否指向 seed stability plan。
  - 输出补充 seed、接受规则、non-goals 和 next action。

- `src/minigpt/model_capability_required_term_pair_readiness_objective_level_contrast_seed_stability_plan_artifacts.py`
  - 输出 JSON、CSV、TXT、Markdown 和 HTML。
  - HTML 展示状态卡、接受规则、后续 artifact、检查行和 non-goals。

- `scripts/run_model_capability_required_term_pair_readiness_objective_level_contrast_seed_stability_plan.py`
  - CLI 入口。
  - 支持输入 promotion guard JSON 或目录，支持 `--require-pass` 和 `--force`。

- `tests/test_model_capability_required_term_pair_readiness_objective_level_contrast_seed_stability_plan.py`
  - 覆盖 ready plan、promotion 已允许时失败、后续 artifact 列表、locator 和 render 输出。

## 核心数据结构

输出的 `plan` 字段是本版主要产物：

```text
source_seed=3636
additional_seeds=[3737, 3838]
required_seed_count=3
minimum_ready_replay_count=2
required_next_artifacts=[
  pair_readiness_objective_level_contrast_seed_3737_training_run,
  pair_readiness_objective_level_contrast_seed_3737_pair_probe_replay,
  pair_readiness_objective_level_contrast_seed_3838_training_run,
  pair_readiness_objective_level_contrast_seed_3838_pair_probe_replay,
  pair_readiness_objective_level_contrast_seed_stability_rollup
]
```

这里的 `source_seed` 指 v763 已完成的训练 seed；`additional_seeds` 是接下来要真实训练和 replay 的补充 seed；`required_next_artifacts` 则把后续版本的输入输出边界提前固定下来。

## 检查逻辑

v767 的 `_checks()` 保护五件事：

- v766 promotion guard 的 `status` 必须是 `pass`。
- v766 decision 必须是 `pair_readiness_objective_level_contrast_promotion_guard_ready_for_seed_stability`。
- `promotion_guard_ready` 必须为 `True`。
- `promotion_allowed` 必须仍为 `False`，避免单 seed 结果被跳过验证直接接受。
- `required_next_artifact` 必须等于 `pair_readiness_objective_level_contrast_seed_stability_plan`。

这些检查让 v767 只服务于 v766 指出的路线，不会被错误的 guard 产物驱动。

## 输入输出和证据角色

真实运行输入：

```text
e/766/解释/model-capability-required-term-pair-readiness-objective-level-contrast-promotion-guard
```

真实运行输出：

```text
e/767/解释/model-capability-required-term-pair-readiness-objective-level-contrast-seed-stability-plan
```

这些 JSON/CSV/TXT/Markdown/HTML 是后续 seed 训练和 rollup 的计划证据，不是训练结果，也不是最终 acceptance 证据。

## 测试覆盖

Focused tests 覆盖：

- 正常 promotion guard 能生成 ready plan。
- 如果 `promotion_allowed=True`，plan 必须失败。
- 后续 artifact 列表必须包含 seed `3737`、seed `3838` 和最终 rollup。
- 输入目录 locator 和所有 render 输出都能工作。

这组测试保护的是“只有未接受的 guarded candidate 才能进入 seed stability”这条边界。

## 运行证据

真实命令：

```powershell
python -B scripts\run_model_capability_required_term_pair_readiness_objective_level_contrast_seed_stability_plan.py e\766\解释\model-capability-required-term-pair-readiness-objective-level-contrast-promotion-guard --out-dir e\767\解释\model-capability-required-term-pair-readiness-objective-level-contrast-seed-stability-plan --require-pass --force
```

输出核心：

```text
status=pass
decision=pair_readiness_objective_level_contrast_seed_stability_plan_ready
seed_stability_plan_ready=True
source_seed=3636
additional_seed_count=2
model_quality_claim=plan_only
```

Playwright 截图位于：

```text
e/767/图片/v767-objective-level-contrast-seed-stability-plan.png
```

一句话总结：v767 把 objective-level contrast 从 guarded candidate 推进为可执行 seed stability 路线，但仍然没有提前宣布模型能力被接受。
