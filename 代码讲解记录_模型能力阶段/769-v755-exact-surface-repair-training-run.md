# v755 exact-surface repair training run 代码讲解

## 本版目标和边界

v755 的目标是用 v754 训练 corpus 进行真实 tiny 训练，并记录训练脚本内的 heldout direct pair probe 结果。

本版不同于 v754：v754 只是 data artifact，v755 生成 checkpoint、tokenizer、metrics 和 run manifest。但是 v755 仍不是 promotion，因为它还没有经过独立 replay。

## 前置路线

- v753 生成 exact-surface repair contract patch。
- v754 将 contract patch 物化为 7680 行 corpus。
- v755 使用同一 larger-tiny 配置训练，观察 near-exact bridge rows 是否让模型在训练脚本内命中 pair-full。

## 训练配置

v755 延续 v749/v744 配置：

```text
seed=3535
max_iters=1800
eval_iters=2
batch_size=16
block_size=16
n_layer=2
n_head=2
n_embd=96
learning_rate=0.01
max_new_tokens=12
temperature=0.2
top_k=1
device=cpu
```

这样后续可把差异主要归因到 corpus 路线，而不是训练参数变化。

## 核心输出字段

v755 输出：

```text
status=pass
decision=pair_readiness_training_pair_full_observed
checkpoint_exists=True
pair_full_observed=True
default_continuation_hit_count=2
model_quality_claim=direct_pair_probe_hit
```

这些字段说明训练脚本内观察到了 pair-full，但 `model_quality_claim` 仍只是 `direct_pair_probe_hit`。

## 产物角色

v755 输出目录包含：

- `model_capability_required_term_pair_readiness_training_run.json`
  - 训练总报告。

- `pair-readiness-training-run/checkpoint.pt`
  - 下一版独立 replay 的模型输入。

- `pair-readiness-training-run/tokenizer.json`
  - 下一版独立 replay 的 tokenizer 输入。

- `pair-readiness-training-run/run_manifest.json`
  - 记录训练配置、路径和产物。

- `pair-readiness-training-run/metrics.jsonl`
  - 记录训练指标。

## 测试和验证

真实运行命令：

```powershell
python -B scripts\run_model_capability_required_term_pair_readiness_training_run.py e\754\解释\model-capability-required-term-pair-readiness-exact-surface-repair-corpus-materialization --out-dir e\755\解释\model-capability-required-term-pair-readiness-exact-surface-repair-training-run --seed 3535 --max-iters 1800 --eval-iters 2 --batch-size 16 --block-size 16 --n-layer 2 --n-head 2 --n-embd 96 --learning-rate 0.01 --max-new-tokens 12 --temperature 0.2 --top-k 1 --device cpu --require-pass --force
```

Playwright 快照确认 HTML 中可见：

- `Decision pair_readiness_training_pair_full_observed`
- `Checkpoint True`
- `Pair-full True`
- default variant 命中 `fixed` 和 `loss`
- suppress-newline variant 命中 `fixed` 和 `loss`

截图位于：

```text
e/755/图片/v755-exact-surface-repair-training-run.png
```

## 证据链角色

v755 是 exact-surface repair route 的训练观察层。它把 v753/v754 的数据路线连接到真实 checkpoint，但必须经过 v756 独立 replay 才能判断 exact heldout prompt 是否真正改善。

一句话总结：v755 将 exact-surface repair route 推进到正向训练观察，但 promotion 仍要等待独立 replay。
