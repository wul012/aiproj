# v814 route promotion bounded real replay repair training run revision 代码讲解

## 本版目标和边界

v814 用 v813 revised seed corpus 做一次真实 tiny training，并生成训练证据。它的目标是产出新的 repair checkpoint revision，让下一版可以拿它跑 bounded real replay。

本版不证明模型能力提升。训练 loss 下降、checkpoint 存在、manifest 完整，都只属于训练产物证据。能力结论必须由下一版 replay comparison 给出。

## 前置链路

- v811：证明 v810 repair checkpoint 退步。
- v812：把 regression 变成 repair strategy revision。
- v813：把 strategy revision 变成 revised corpus，包含 baseline preservation。
- v814：用 revised corpus 训练新的 checkpoint，并记录证据。

这条链路刻意避免“训练即提升”的误判。

## 关键文件

- `src/minigpt/model_capability_route_promotion_bounded_real_replay_repair_training_run_revision.py`
  - 核心 evidence builder。
  - 读取 seed revision 和训练 run 目录。
  - 检查 checkpoint、tokenizer、metrics、manifest、prepared corpus 是否存在。
  - 读取 `metrics.jsonl`，计算 train/val loss delta。

- `src/minigpt/model_capability_route_promotion_bounded_real_replay_repair_training_run_revision_artifacts.py`
  - 输出 JSON/CSV/text/Markdown/HTML。
  - HTML 只展示训练产物，不展示模型能力结论。

- `scripts/build_model_capability_route_promotion_bounded_real_replay_repair_training_run_revision.py`
  - CLI 入口。
  - 支持 `--seed-revision`、`--run-dir`、`--out-dir`、`--require-training-revision-ready`。
  - 修复了 `--force` 删除嵌套 `run/` 的问题。

- `tests/test_model_capability_route_promotion_bounded_real_replay_repair_training_run_revision.py`
  - 覆盖 ready evidence、缺 checkpoint 失败、CLI 输出、force 保留嵌套 run。

## 核心检查

v814 的 `_checks()` 包含：

- `seed_revision_passed`
- `seed_revision_ready`
- `baseline_preservation_present`
- `checkpoint_exists`
- `tokenizer_exists`
- `metrics_exists`
- `manifest_exists`
- `prepared_corpus_exists`
- `metrics_records_present`
- `max_iters_positive`

其中 `baseline_preservation_present` 是本版关键：只有 revised seed 中包含 baseline preservation example，训练证据才算 ready。这样能防止后续又用没有保底样本的语料继续训练。

## CLI force 修复

本版遇到并修复了一个真实问题：如果 training evidence 输出目录和训练 run 父目录相同，例如：

```text
e/814/解释/.../training-run-revision/
  run/
  model_capability_...json
```

旧 `--force` 会删除整个输出目录，导致 `run/` 也被删掉。v814 把 `prepare_output_dir()` 改为支持 `preserve_dir`：

- 如果 `run_dir` 位于 `out_dir` 内部，只删除其他旧 report 文件。
- 保留 `run/` 目录。
- 如果 `run_dir` 不在 `out_dir` 内，保持原来的整目录替换逻辑。

测试 `test_cli_force_preserves_nested_run_dir` 覆盖了这个风险。

## 真实训练结果

真实训练使用 v813 corpus：

```text
tokens=1755
vocab_size=74
parameters=28864
step=1  train_loss=4.2707 val_loss=4.2732
step=25 train_loss=3.9683 val_loss=3.9442
```

evidence summary：

```text
training_revision_ready=True
final_step=25
final_train_loss=3.968329429626465
final_val_loss=3.9442343711853027
seed_revision_example_count=18
baseline_preservation_example_count=2
next_step=run_repair_checkpoint_revision_bounded_replay
```

这些数字说明训练产物完成，但不代表 replay case 会通过。下一版要用 checkpoint 和 tokenizer 跑同一套 bounded benchmark。

## 产物角色

- `run/checkpoint.pt`：下一版 replay 的候选 checkpoint。
- `run/tokenizer.json`：与 checkpoint 配套的 tokenizer。
- `run/metrics.jsonl`：训练过程指标。
- `run/run_manifest.json`：训练参数和环境记录。
- `model_capability_route_promotion_bounded_real_replay_repair_training_run_revision.json`：结构化 evidence。
- HTML 和截图：人工审查证据。

## 测试覆盖

测试覆盖三类风险：

- 正常 fake run 能生成 ready evidence。
- 删除 checkpoint 后 evidence 失败。
- CLI `--force` 不会删除嵌套 `run/`。

第三条是本版实际踩到的问题，因此它比普通 artifact 测试更有维护价值。

## 一句话总结

v814 产出了 revised repair checkpoint，并把训练 evidence 与模型质量结论彻底拆开，为下一版真实 replay comparison 留出清晰边界。
