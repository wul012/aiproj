# v763 objective-level contrast training run 代码讲解

## 本版目标和边界

v763 的目标是对 v762 训练 corpus 跑一次真实 tiny training，并记录 checkpoint、metrics、direct replay 和 HTML 报告。

本版不是 promotion。它只说明 objective-level contrast corpus 在训练运行内能让 `fixed=` 和 `loss=` direct probes 都命中。pair prompt 是否迁移，要交给下一版独立 replay。

## 前置路线

- v761：生成 objective-level contrast contract。
- v762：物化 8320 行训练 corpus 和 heldout fixture。
- v763：训练 fresh tiny checkpoint 并跑 direct probes。

## 关键产物

- `e/763/解释/model-capability-required-term-pair-readiness-objective-level-contrast-training-run/model_capability_required_term_pair_readiness_training_run.json`
  - v763 主报告。
  - 记录训练参数、训练产物路径、direct replay 结果和 summary。

- `e/763/解释/model-capability-required-term-pair-readiness-objective-level-contrast-training-run/pair-readiness-training-run/checkpoint.pt`
  - 真实训练出来的 tiny checkpoint。

- `e/763/解释/model-capability-required-term-pair-readiness-objective-level-contrast-training-run/pair-readiness-training-run/tokenizer.json`
  - 与 checkpoint 配套的 tokenizer。

- `e/763/解释/model-capability-required-term-pair-readiness-objective-level-contrast-training-run/heldout-direct-replay`
  - 训练脚本内 direct probes replay 产物。

## 训练参数

```text
seed=3636
max_iters=1800
batch_size=16
block_size=16
n_layer=2
n_head=2
n_embd=96
learning_rate=0.01
temperature=0.2
top_k=1
device=cpu
```

这些参数沿用最近 larger-tiny 可比配置，目的是让 v763 可以和 v755、v749 等训练结果保持可比，而不是靠更大模型掩盖数据路线差异。

## 结果解释

v763 输出：

```text
decision=pair_readiness_training_pair_full_observed
checkpoint_exists=True
pair_full_observed=True
default_continuation_hit_count=2
model_quality_claim=direct_pair_probe_hit
```

这里的 pair-full 指 direct probes 两个 term 都命中，不等于 heldout pair prompt 已经通过。报告里的 next action 已经明确写出：`run heldout pair-probe replay before promoting the checkpoint`。

## 测试和验证

真实运行命令：

```powershell
python -B scripts\run_model_capability_required_term_pair_readiness_training_run.py e\762\解释\model-capability-required-term-pair-readiness-objective-level-contrast-corpus-materialization --out-dir e\763\解释\model-capability-required-term-pair-readiness-objective-level-contrast-training-run --seed 3636 --max-iters 1800 --eval-iters 2 --batch-size 16 --block-size 16 --n-layer 2 --n-head 2 --n-embd 96 --learning-rate 0.01 --max-new-tokens 12 --temperature 0.2 --top-k 1 --device cpu --require-pass --force
```

Playwright 快照确认 HTML 中可见：

- `Decision pair_readiness_training_pair_full_observed`
- `Checkpoint True`
- `Pair-full True`
- `Claim direct_pair_probe_hit`

截图位于：

```text
e/763/图片/v763-objective-level-contrast-training-run.png
```

## 证据链角色

v763 是真实训练层。它证明 objective-level contrast corpus 能训练出 direct pair hit，但还没有通过独立 pair replay，因此后续必须先做 replay 再谈路线有效性。

一句话总结：v763 产生了一个 direct-hit tiny checkpoint，并把它交给下一版做独立 pair-probe replay。
