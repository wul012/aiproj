# v670 required-term pair dual-objective boundary plan

## 本版目标和边界

v670 将 v666 closeout 和 v669 miss diagnostic 合成 explicit dual-objective boundary plan。目标是给下一版 corpus mode 一个清晰约束，而不是继续按经验堆训练文本。

本版不训练模型，不新增 corpus mode，不声称模型能力提升。

## 输入证据

### v666 closeout

v666 确认：

- naive checkpoint continuation 已关闭。
- `selected_generation_route=loss-internal-joint-cycle`
- `internal_anchor_route=joint-cycle-internal-repair`
- 下一步应转向 constrained decode 或 explicit dual-objective boundary。

### v669 miss diagnostic

v669 确认：

- constrained decode 只恢复 loss。
- fixed 仍 miss。
- fixed miss class 是 `prefix_fragment_without_full_term`。
- 推荐下一步为 `explicit_dual_objective_boundary_for_fixed_retention`。

## 关键新增文件

### `src/minigpt/model_capability_required_term_pair_dual_objective_boundary_plan.py`

核心 builder 是 `build_model_capability_required_term_pair_dual_objective_boundary_plan()`。

它生成：

- `proposed_corpus_mode`
- `constraints`
- `summary`
- `interpretation`

本版 proposed corpus mode 是：

```text
equals_surface_no_pair_id_loss_internal_explicit_dual_boundary_repair
```

约束包括：

- 保留 generation anchor。
- 保留 internal anchor。
- 修复 constrained decode 后仍 miss 的 fixed。
- 保留 constrained decode 已恢复的 loss。
- 避免继续 naive resume。

### `src/minigpt/model_capability_required_term_pair_dual_objective_boundary_plan_artifacts.py`

负责输出 JSON/CSV/text/Markdown/HTML，HTML 报告显示 constraint table 和 next action。

### `scripts/run_model_capability_required_term_pair_dual_objective_boundary_plan.py`

新增 CLI：

```powershell
python -B scripts\run_model_capability_required_term_pair_dual_objective_boundary_plan.py --closeout <closeout> --miss-diagnostic <diagnostic> --out-dir <dir> --require-pass --force
```

## 运行结果

本版输出：

- `decision=explicit_dual_objective_boundary_plan_ready`
- `constraint_count=5`
- `fixed_miss_class=prefix_fragment_without_full_term`
- `loss_constrained_hit=True`
- `ready_to_add_corpus_mode=True`

## 测试覆盖

新增测试文件：

```text
tests/test_model_capability_required_term_pair_dual_objective_boundary_plan.py
```

覆盖内容：

- fixed miss + loss constrained hit 时 plan ready。
- fixed 不再是 remaining miss 时失败。
- 五种 artifact 格式渲染。
- closeout 与 miss diagnostic locator 支持目录输入。

运行结果：`4 passed`。

## 证据归档

- JSON/CSV/text/Markdown/HTML: `e/670/解释/model-capability-required-term-pair-dual-objective-boundary-plan/`
- 截图: `e/670/图片/v670-dual-objective-boundary-plan.png`
- 解释: `e/670/解释/说明.md`

一句话总结：v670 把“下一步该怎么修”从口头判断变成了可执行、可测试的 corpus plan。
