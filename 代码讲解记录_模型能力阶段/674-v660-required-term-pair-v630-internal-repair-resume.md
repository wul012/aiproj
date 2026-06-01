# v660 required-term pair v630 internal-repair resume

## 本版目标和边界

v660 用 v659 新增的 `--resume-checkpoint` 跑第一条真实 checkpoint continuation。起点是 v630 的 `loss-internal-joint-cycle` checkpoint，它曾经提供 generation pair-full；续训语料使用 v640 风格的 internal-repair mode。

本版不是从头训练，也不是单语料近似，而是真正加载 v630 checkpoint 和 optimizer 后继续训练。

## 运行配置

- resume checkpoint：`e/630/.../pair-coexistence-refresh-run/checkpoint.pt`
- corpus mode：`equals_surface_no_pair_id_loss_internal_joint_cycle_internal_repair`
- seed：`3535`
- max iters：`2200`
- learning rate：`0.005`
- device：`cpu`

## 核心结果

报告字段确认：

- `training_mode=checkpoint_continuation`
- `resume_checkpoint_exists=True`
- `checkpoint_exists=True`

能力结果：

- `pair_full_observed=False`
- `fixed=` 未命中。
- `loss=` 命中。

这说明续训机制有效，但当前 continuation 目标过度拉向 loss/internal repair，破坏了 v630 原本的 fixed 生成。

## 运行证据

产物写入：

- `e/660/解释/model-capability-required-term-pair-v630-to-internal-repair-resume-seed-3535/`
- `e/660/图片/v660-v630-to-internal-repair-resume.png`

## 一句话总结

v660 证明 required-term pair 真实续训可运行，但 naive internal-repair continuation 会把 pair-full 退化成 loss-only。
