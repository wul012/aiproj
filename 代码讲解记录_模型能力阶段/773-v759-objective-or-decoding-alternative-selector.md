# v759 objective-or-decoding alternative selector 代码讲解

## 本版目标和边界

v759 的目标是给 v758 closeout 后的三条候选路线做排序和选择。v758 已经关闭 `near_exact_surface_bridge_rows`，但它只给出了 candidate routes；v759 把这个口头候选变成 JSON/CSV/HTML 可审计证据，并选出下一版的具体 artifact。

本版不训练模型，不新增样本，不调整生成器。它的结论是 selection-only：选择路线，不声明模型能力提升。

## 前置路线

- v757：证明 exact-surface repair route 没有 replay 改善。
- v758：关闭 near-exact surface bridge rows，列出 objective、decoding、fresh-seed 三条候选路线。
- v759：对三条候选路线评分，选择 `objective_level_contrast`。

## 关键新增文件

- `src/minigpt/model_capability_required_term_pair_readiness_objective_or_decoding_alternative_selector.py`
  - 选择器核心。
  - 输入 v758 route closeout。
  - 校验 closeout status、decision、closed route、recommended next route 和候选路线完整性。
  - 给每个候选路线计算固定、透明的工程分数。

- `src/minigpt/model_capability_required_term_pair_readiness_objective_or_decoding_alternative_selector_artifacts.py`
  - 输出 JSON、CSV、TXT、Markdown 和 HTML。
  - HTML 展示 route scores、non-goals、checks 和 next action。

- `scripts/run_model_capability_required_term_pair_readiness_objective_or_decoding_alternative_selector.py`
  - CLI 入口。
  - 支持输入 v758 JSON 或目录。
  - `--require-pass` 下 selector check 失败会返回非 0。

- `tests/test_model_capability_required_term_pair_readiness_objective_or_decoding_alternative_selector.py`
  - 覆盖正常选择、错误 recommended route 失败、route score 顺序和 artifact 输出。

## 输入输出结构

输入来自 v758：

```text
status=pass
decision=pair_readiness_exact_surface_repair_route_closed
closed_route=near_exact_surface_bridge_rows
recommended_next_route=objective_or_decoding_alternative_plan
candidate_route_count=3
```

v759 输出：

```text
decision=pair_readiness_objective_or_decoding_alternative_selected
selected_route=objective_level_contrast
selected_score=92
proposed_next_artifact=pair_readiness_objective_level_contrast_plan
```

## 路线评分解释

| route | score | 本版判断 |
| --- | ---: | --- |
| objective_level_contrast | 92 | 改变训练目标，最符合 v758“不要继续 surface rows”的边界 |
| decode_side_constraint_probe | 78 | 适合诊断 first-token/separator 敏感性，但不能作为 promotion 证据 |
| fresh_seed_stability | 64 | 能复验 seed 偶然性，但在没有新假设前训练成本偏高 |

`non_goals` 同时约束了三件事：不再添加 near-exact rows，不把 constrained decoding 当作能力证明，不在路线假设变清晰前先做 fresh-seed 训练。

## 测试和验证

Focused tests：

```powershell
python -m pytest tests\test_model_capability_required_term_pair_readiness_objective_or_decoding_alternative_selector.py -q -o cache_dir=runs\pytest-cache-v759-focused
```

结果为 4 个测试通过。

真实运行命令：

```powershell
python -B scripts\run_model_capability_required_term_pair_readiness_objective_or_decoding_alternative_selector.py e\758\解释\model-capability-required-term-pair-readiness-exact-surface-repair-route-closeout --out-dir e\759\解释\model-capability-required-term-pair-readiness-objective-or-decoding-alternative-selector --require-pass --force
```

Playwright 快照确认 HTML 中可见：

- `Decision pair_readiness_objective_or_decoding_alternative_selected`
- `Selected objective_level_contrast`
- `Score 92`
- `Next pair_readiness_objective_level_contrast_plan`

截图位于：

```text
e/759/图片/v759-objective-or-decoding-alternative-selector.png
```

## 证据链角色

v759 是路线选择层。它避免“凭直觉选下一步”，把 v758 的候选方向变成有 checks、有分数、有 non-goals 的可追踪 artifact。

一句话总结：v759 选择 objective-level contrast 作为下一条主线，为 v760 的目标设计计划提供稳定入口。
