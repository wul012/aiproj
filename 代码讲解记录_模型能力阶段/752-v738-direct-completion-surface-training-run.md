# v738 direct-completion surface training run

## 本版目标和边界

v738 的目标是用 v737 物化出的 direct-completion surface corpus 做一次真实 tiny GPT 训练。

本版不是 contract、不是计划、不是静态报告，而是实际运行训练脚本并产出 checkpoint、metrics、manifest、HTML 报告和 replay 结果。它可以作为模型能力证据，但边界也要清楚：这只证明 heldout direct probes 出现 pair-full，不等于可以直接 promotion。

## 前置链路

```text
v736 direct-completion surface contract
 -> fixed=fixed / loss=loss + balanced prefix ladders
v737 corpus materialization
 -> 5120 training lines + heldout eval fixture
v738 training run
 -> checkpoint + heldout direct replay
```

## 训练配置

v738 沿用 v729/v733 的 larger tiny 配置，保证比较时不混入模型容量变化：

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

这意味着 v738 的变量主要是 corpus surface，而不是模型结构。

## 关键输出

输出目录：

```text
e/738/解释/model-capability-required-term-pair-readiness-direct-completion-surface-training-run/
```

关键文件：

- `checkpoint.pt`
  - 本次真实训练得到的模型权重。
- `tokenizer.json`
  - 本次训练使用的 tokenizer。
- `metrics.jsonl`
  - 训练过程指标。
- `history_summary.json`
  - loss 历史摘要。
- `run_manifest.json`
  - 训练参数、输入、环境和产物清单。
- `model_capability_required_term_pair_readiness_training_run.json`
  - pair-readiness 训练主报告。
- `model_capability_required_term_pair_readiness_training_run.html`
  - 浏览器截图证据来源。

## 核心结果

命令行摘要：

```text
status=pass
decision=pair_readiness_training_pair_full_observed
training_status=pass
checkpoint_exists=True
pair_full_observed=True
default_continuation_hit_count=2
model_quality_claim=direct_pair_probe_hit
```

JSON summary 进一步显示：

```text
default_pair_full_variant_count=1
suppression_pair_full_variant_count=1
default_continuation_hit_count=2
suppression_continuation_hit_count=2
pair_full_observed=True
```

这里的意义是：default replay 和 suppress-newline replay 都保留 pair-full，而不是只有一个 profile 偶然命中。

## 与上一条路线的差异

v733 direct-prompt bridge training 的结果是：

```text
pair_full_observed=False
default_continuation_hit_count=0
```

v738 direct-completion surface training 的结果是：

```text
pair_full_observed=True
default_continuation_hit_count=2
```

因此 v738 是 direct-completion surface route 的第一条正向模型能力证据。

## 为什么还不能直接 promotion

v738 的下一步是：

```text
run heldout pair-probe replay before promoting the checkpoint
```

原因：

- 当前报告主要看 heldout direct probes：`fixed=` 和 `loss=`。
- pair heldout probe `fixed=|loss=` 仍需单独 replay 或比较报告确认。
- 还需要和 v729/v733/v724 等历史路线放在同一比较矩阵中，确认提升不是口径差异。

## 证据

运行截图：

```text
e/738/图片/v738-direct-completion-surface-training-run.png
```

截图中可见：

- `Status=pass`
- `Decision=pair_readiness_training_pair_full_observed`
- `Checkpoint=True`
- `Pair-full=True`
- `Claim=direct_pair_probe_hit`

## 一句话总结

v738 把 direct-completion surface route 从数据假设推进为真实正向 tiny 训练证据，但 promotion 前仍需要 pair-probe replay 和历史路线比较。
