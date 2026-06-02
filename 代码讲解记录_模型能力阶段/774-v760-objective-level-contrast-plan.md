# v760 objective-level contrast plan 代码讲解

## 本版目标和边界

v760 的目标是把 v759 选中的 `objective_level_contrast` 路线变成 contract 前计划。v759 只回答“选哪条路线”，v760 回答“这条路线下一份 contract 要怎么设计”。

本版不训练模型，不物化 corpus，也不增加 near-exact surface rows。它输出的是 plan-only 证据，用来约束 v761 的 contract 实现。

## 前置路线

- v758：关闭 near-exact surface bridge rows。
- v759：在 objective、decoding、fresh-seed 三条路线中选择 `objective_level_contrast`。
- v760：把选择结果转为 objective-level contrast contract 计划。

## 关键新增文件

- `src/minigpt/model_capability_required_term_pair_readiness_objective_level_contrast_plan.py`
  - 计划核心逻辑。
  - 输入 v759 selector。
  - 校验 selector status、decision、ready、selected route、selected score 和唯一 selected row。
  - 输出 contract design rows、heldout boundaries、acceptance checks 和 non-goals。

- `src/minigpt/model_capability_required_term_pair_readiness_objective_level_contrast_plan_artifacts.py`
  - 输出 JSON、CSV、TXT、Markdown 和 HTML。
  - CSV 记录四个 contract row family。
  - HTML 展示 row family、heldout boundaries、acceptance checks 和 input checks。

- `scripts/run_model_capability_required_term_pair_readiness_objective_level_contrast_plan.py`
  - CLI 入口。
  - 支持输入 v759 JSON 或目录。
  - `--require-pass` 下计划检查失败返回非 0。

- `tests/test_model_capability_required_term_pair_readiness_objective_level_contrast_plan.py`
  - 覆盖 ready plan、错误 selected route 失败、heldout/non-goals 保留和 artifact 输出。

## 输入输出结构

输入来自 v759：

```text
decision=pair_readiness_objective_or_decoding_alternative_selected
selector_ready=True
selected_route=objective_level_contrast
selected_score=92
proposed_next_artifact=pair_readiness_objective_level_contrast_plan
```

v760 输出：

```text
decision=pair_readiness_objective_level_contrast_plan_ready
proposed_next_artifact=pair_readiness_objective_level_contrast_contract
contract_design_row_count=4
planned_training_row_count=26
```

## contract design rows

| row family | count | 作用 |
| --- | ---: | --- |
| objective-header | 6 | 在 answer text 前显式写出响应目标 |
| branch-role-contrast | 8 | 用 task id 对比 fixed/loss 分支角色 |
| pair-answer-contrast | 8 | 通过不同 objective label 请求两个 answer terms |
| separator-neutral-answer | 4 | 使用非 heldout separator 训练答案组合 |

这 26 行只是计划数量，不是最终 corpus。v761 contract 需要把这些计划变成实际 rows，并做泄漏检查。

## heldout 边界和 non-goals

heldout boundaries：

- exact-heldout-pair prompt surface remains eval-only
- spaced-heldout-pair prompt surface remains eval-only
- arrow-heldout-pair prompt surface remains eval-only

non-goals：

- 不再加 near-exact bridge row patch。
- 不在 objective contract replay 前改变模型大小。
- 不把 constrained decoding 当作模型质量证据。

## 测试和验证

Focused tests：

```powershell
python -m pytest tests\test_model_capability_required_term_pair_readiness_objective_level_contrast_plan.py -q -o cache_dir=runs\pytest-cache-v760-focused
```

结果为 4 个测试通过。

真实运行命令：

```powershell
python -B scripts\run_model_capability_required_term_pair_readiness_objective_level_contrast_plan.py e\759\解释\model-capability-required-term-pair-readiness-objective-or-decoding-alternative-selector --out-dir e\760\解释\model-capability-required-term-pair-readiness-objective-level-contrast-plan --require-pass --force
```

Playwright 快照确认 HTML 中可见：

- `Decision pair_readiness_objective_level_contrast_plan_ready`
- `Rows 26`
- `Next pair_readiness_objective_level_contrast_contract`
- heldout boundaries 和 acceptance checks。

截图位于：

```text
e/760/图片/v760-objective-level-contrast-plan.png
```

## 证据链角色

v760 是 contract design gate。它让 v761 不能随意写 rows，而必须遵守 objective-level contrast、heldout eval-only、balanced row count 和 materializer-compatible 四类约束。

一句话总结：v760 把选中的 objective-level contrast 路线固化为可实现、可检查、可追溯的 contract 计划。
