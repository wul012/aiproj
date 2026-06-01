# v651 required-term pair surface-first schedule seed 3535

## 本版目标和边界

v651 的目标是运行 v650 新 corpus mode 的真实 tiny 训练，观察它是否能把 v649 的两阶段计划转化为生成侧 `fixed/loss` pair-full。

本版是训练证据，不是治理报告。它只证明这一组 seed/config 下的行为，不推广到更大模型或更多训练轮次。

## 输入和输出

输入：

- corpus mode：`equals_surface_no_pair_id_loss_internal_surface_first_schedule_repair`
- seed：`3535`
- 训练配置：1 层、1 头、64 维 embedding、1800 iter、CPU。

输出：

- `model_capability_required_term_pair_coexistence_refresh.json`
- `model_capability_required_term_pair_coexistence_refresh.md`
- `model_capability_required_term_pair_coexistence_refresh.html`
- `pair-coexistence-refresh-run/checkpoint.pt`
- `pair-coexistence-refresh-run/tokenizer.json`

## 核心结果

报告显示：

- `status=pass`
- `training_status=pass`
- `checkpoint_exists=True`
- `decision=required_term_pair_coexistence_refresh_no_pair_full`
- `pair_full_observed=False`

Replay 的具体行为：

- `fixed=` 可以命中 `fixed`。
- `loss=` 输出 `fixedatfixed`，没有命中 `loss`。

这不是失败的工程运行，而是失败的模型候选：训练流程完整，但目标能力没有出现。

## 为什么这个结果重要

v649 的计划是基于两条路线互补：

- v630/v631：生成 pair-full，但内部 forced-choice 不完整。
- v640/v641：内部 forced-choice pair-full，但生成侧断掉。

v651 证明把两类文本简单合并成 surface-first 语料，并不能恢复两边优势。它让后续方向更明确：如果继续做 schedule，需要更强的阶段隔离、真正 checkpoint continuation，或更可控的采样/解码约束。

## 测试和证据

运行证据写入：

- `e/651/解释/model-capability-required-term-pair-surface-first-schedule-seed-3535/`
- `e/651/图片/v651-surface-first-schedule-seed-3535.png`

截图证明 HTML 可以直接看到：

- Training=`pass`
- Checkpoint=`True`
- Pair full observed=`False`

## 一句话总结

v651 用真实训练证实 surface-first approximation 仍是 fixed-only，不应作为 pair-full 候选推进。
