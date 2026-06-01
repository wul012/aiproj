# v666 required-term pair resume branch closeout

## 本版目标和边界

v666 目标是关闭 v659-v666 的 real checkpoint continuation 分支。

这个分支已经回答了两个问题：

- 工程上，`--resume-checkpoint` 路径可以真实加载 checkpoint 并继续训练。
- 模型上，naive continuation 没有产生 aligned pair-full，反而让 v630 的 generation pair-full 退化。

本版不训练新 checkpoint，也不继续试一个轻微参数变体。它把已有 evidence 收束成正式 closeout。

## 关键修改

### `src/minigpt/model_capability_required_term_pair_generation_internal_batch_closeout.py`

原 closeout 工具已经支持 `batch_start`、`batch_end` 和 `next_route`，但部分输出文案仍绑定旧批次：

- decision 默认落回 `close_batch_and_design_joint_cycle_internal_repair`
- closeout items 里有 balanced-anchor 的历史说明
- interpretation 的 next_action 只特殊处理 two-stage schedule

v666 将这些逻辑泛化：

- `_decision()` 直接使用 `next_route` 生成 closeout decision。
- `_interpretation()` 输出 `design <next_route>`。
- `_closeout_items()` 使用 selected generation route 和 internal anchor 的实际 label。
- 当 source label 包含 `resume` 时，增加 `resume_routes_rejected`。

这让同一个 closeout 工具可以服务 v629-v638、v639-v648、v659-v666 这类不同分支，而不是为每个分支复制一份新模块。

### `tests/test_model_capability_required_term_pair_generation_internal_batch_closeout.py`

新增测试覆盖：

- 自定义 `next_route` 会进入 interpretation。
- 带有 resume source 的 comparison 会生成 `resume_routes_rejected`。
- custom batch range 包含 `v666`。

这些断言保护了 v666 的核心语义：resume 失败是正式比较过的路线，不是缺失输入。

## 运行命令

```powershell
python -B scripts\run_model_capability_required_term_pair_generation_internal_batch_closeout.py --comparison e\664\解释\model-capability-required-term-pair-alignment-comparison-with-resume-routes --route-decision e\665\解释\model-capability-required-term-pair-route-decision-with-resume-routes --batch-start 659 --batch-end 666 --next-route constrained_decode_or_explicit_dual_objective_boundary --out-dir e\666\解释\model-capability-required-term-pair-resume-branch-closeout --require-pass --force
```

## 核心输出字段

- `status=pass`
- `decision=close_batch_and_design_constrained_decode_or_explicit_dual_objective_boundary`
- `batch_version_count=8`
- `aligned_pair_full_count=0`
- `selected_generation_route=loss-internal-joint-cycle`
- `internal_anchor_route=joint-cycle-internal-repair`
- `next_action=design constrained_decode_or_explicit_dual_objective_boundary`

## 链路角色

v666 是一个 stop signal。它不是因为 continuation 不能跑才停止，而是因为 continuation 已经被真实训练、forced-choice、alignment matrix、route decision 四层证据检查过，仍未超过既有 split anchors。

因此后续路线应避免继续碎片化尝试：

- 不继续堆 lower-rate resume。
- 不继续堆 light-merge resume。
- 不把 single-corpus schedule approximation 当作真正两阶段训练。
- 转向 constrained decode 或显式 dual-objective boundary。

## 测试与归档

运行测试：

```powershell
python -m pytest tests\test_model_capability_required_term_pair_generation_internal_batch_closeout.py -q -o cache_dir=runs\pytest-cache-v666-closeout
```

结果为 `5 passed`。

归档：

- 运行解释：`e/666/解释/说明.md`
- HTML evidence：`e/666/解释/model-capability-required-term-pair-resume-branch-closeout/`
- 截图：`e/666/图片/v666-resume-branch-closeout.png`

一句话总结：v666 用复用并泛化后的 closeout 工具，把 real checkpoint continuation 分支正式关闭为负证据。
