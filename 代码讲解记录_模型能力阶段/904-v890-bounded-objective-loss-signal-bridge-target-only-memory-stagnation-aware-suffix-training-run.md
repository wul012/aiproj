# v890 stagnation-aware suffix training run 代码讲解

## 本版目标和边界

v890 承接 v889 patch。v889 已经把 stagnation-aware repair plan 落成了 27 条 no-anchor patch examples，v890 的目标是把这份 corpus 训练成真实 checkpoint，并完整记录训练产物。

本版不做 replay，不做 holdout，也不声称模型恢复。尤其要注意，本版 sample 并没有输出完整 `fixed loss`，所以模型能力判断必须交给 v891 replay。

## 关键文件

- `src/minigpt/bounded_objective_loss_signal_bridge_target_only_memory_stagnation_aware_suffix_training_run.py`
  - 把 v889 patch report 适配到通用 loss-signal bridge training builder。
  - 输出 v890 专属 decision、summary、interpretation。
- `src/minigpt/bounded_objective_loss_signal_bridge_target_only_memory_stagnation_aware_suffix_training_run_artifacts.py`
  - 写出 JSON、CSV、TXT、Markdown、HTML。
- `scripts/build_bounded_objective_loss_signal_bridge_target_only_memory_stagnation_aware_suffix_training_run.py`
  - CLI 入口，读取 v889 patch 和训练 run 目录。
- `tests/test_bounded_objective_loss_signal_bridge_target_only_memory_stagnation_aware_suffix_training_run.py`
  - 覆盖 ready、not-ready、CLI 和 artifact 输出。

## 核心适配

v889 patch 的 summary 包含：

```text
patch_example_count=27
replay_prompt_boundary_example_count=6
suffix_position_example_count=12
training_corpus_ratio_example_count=4
surface_format_example_count=4
decoder_anchor_example_count=0
```

v890 把训练中的 `loss_signal_bridge_example_count` 设置为：

```text
6 + 12 + 4 = 22
```

这里没有把 `surface_format_example_count=4` 算进去，因为它主要是格式保持，不是 suffix uptake 的核心信号。这个区分能让训练报告更真实地表达“哪些样本真正服务于 suffix 恢复”。

## 本版真实训练

训练参数：

```text
tokenizer=char
batch_size=8
block_size=64
max_iters=280
n_layer=2
n_head=2
n_embd=64
device=cpu
seed=1890
```

结果：

```text
final_step=280
final_train_loss=0.4759935438632965
final_val_loss=0.44544440507888794
train_loss_delta=-3.207202
val_loss_delta=-3.233418
repair_example_count=27
neutral_prompt_example_count=22
decoder_anchor_example_count=0
```

sample 输出：

```text
Answer with exactly two tokens: fixed loss answer:
answer: fix
```

这个 sample 是负向提醒：训练 loss 下降不等价于 contract 恢复，下一版 replay 更重要。

## 测试覆盖

测试保护三件事：

- v889 patch ready 时，v890 training report ready，并路由到 replay comparison。
- patch ready 被置为 false 时，报告转入修复决策。
- CLI 能从 patch 目录定位 JSON，并写出五类 report artifact。

额外断言 `neutral_prompt_example_count=22`，避免 surface-format 样本被误算成 suffix 信号。

## 一句话总结

v890 把 v889 patch 训练成真实 checkpoint，但 sample 没有恢复完整目标，能力判断仍必须由 v891 replay 完成。
