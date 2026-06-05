# v881：bounded objective loss signal bridge target-only memory completion-surface stabilization training run

## 本版目标和边界

v881 的目标是训练 v880 completion-surface stabilization patch corpus，产出真实 tiny checkpoint 和训练证据。v880 只是语料 patch，v881 才是实际训练运行。

本版不做 replay，不修改 v836 contract，不声称能力恢复。即使 sample 输出 `fixed loss`，也只能写成 `training_artifact_only`，因为固定 objective cases 必须由 v882 replay 验证。

## 前置链路

```text
v879 replay regression diagnostic
 -> v880 completion-surface stabilization patch
 -> v881 completion-surface stabilization training run
 -> v882 completion-surface stabilization replay comparison
```

v881 的职责是把 patch 转成 checkpoint，下一版再回答“checkpoint 是否真的修复了 completion surface 和 full contract”。

## 关键新增文件

- `src/minigpt/bounded_objective_loss_signal_bridge_target_only_memory_completion_surface_stabilization_training_run.py`
  - v881 training report adapter。
  - 将 v880 patch summary 映射到通用 `bounded_objective_loss_signal_bridge_training_run`。
  - 把 next artifact 改成 `bounded_objective_loss_signal_bridge_target_only_memory_completion_surface_stabilization_replay_comparison`。

- `src/minigpt/bounded_objective_loss_signal_bridge_target_only_memory_completion_surface_stabilization_training_run_artifacts.py`
  - 复用 loss-signal bridge training renderer。
  - 替换 ready 字段和标题为 completion-surface stabilization training run。

- `scripts/build_bounded_objective_loss_signal_bridge_target_only_memory_completion_surface_stabilization_training_run.py`
  - 将真实 `run/` 目录和 v880 patch report 合并成 v881 JSON/CSV/TXT/Markdown/HTML 报告。

- `tests/test_bounded_objective_loss_signal_bridge_target_only_memory_completion_surface_stabilization_training_run.py`
  - 覆盖 training ready、patch not ready fail、writer 和 CLI。

## 真实训练配置

v881 延续 v877 的 tiny CPU 配置：

```text
tokenizer=char
batch_size=8
block_size=64
max_iters=240
eval_interval=10
eval_iters=5
learning_rate=0.001
n_layer=2
n_head=2
n_embd=64
dropout=0.0
seed=1881
device=cpu
```

相比 v877 的 220 steps，v881 用 240 steps，因为 v880 corpus 更聚焦 completion surface，需要稍微多一点训练步数观察稳定性。

## 训练结果

```text
final_step=240
final_train_loss=0.7887188792228699
final_val_loss=0.36948448419570923
train_loss_delta=-2.888267
repair_example_count=28
neutral_prompt_example_count=12
decoder_anchor_example_count=0
```

sample：

```text
Complete with exactly two tokens: fixed loss completion: fixed loss
```

这个 sample 很重要，但边界也很明确：它证明训练产物在 completion prompt 上有直接记忆效果，不证明三条 contract cases 已通过。

## 测试覆盖

focused 测试：

```text
python -m pytest tests/test_bounded_objective_loss_signal_bridge_target_only_memory_completion_surface_stabilization_training_run.py -q -o cache_dir=runs/pytest-cache-v881-focused
```

结果：

```text
3 passed
```

测试保护：

- v880 patch ready 才能生成 ready training report。
- patch not ready 时必须 fail。
- writer 和 CLI 必须输出 JSON、CSV、TXT、Markdown、HTML。
- next artifact 必须指向 v882 replay comparison，而不是直接 promotion。

## 运行证据

- 解释目录：`e/881/解释/bounded-objective-loss-signal-bridge-target-only-memory-completion-surface-stabilization-training-run/`
- run 目录：`e/881/解释/bounded-objective-loss-signal-bridge-target-only-memory-completion-surface-stabilization-training-run/run/`
- 截图目录：`e/881/图片/`
- Playwright MCP 截图：`e/881/图片/v881-bounded-objective-loss-signal-bridge-target-only-memory-completion-surface-stabilization-training-run-html.png`

## 一句话总结

v881 完成了 completion-surface patch 的真实 tiny 训练，把 v880 语料转换成可 replay 的 checkpoint。
