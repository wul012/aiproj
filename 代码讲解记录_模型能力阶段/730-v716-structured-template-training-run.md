# v716 structured-template training run

## 本版目标和边界

v716 的目标是用 v715 materialized corpus 进行真实 tiny training。

本版不是 contract，也不是模拟测试；它实际调用训练链，生成 checkpoint、tokenizer、metrics、sample 和 replay report。

本版不做 promotion，因为 pair-full 没有出现。

## 前置链路

```text
v714 structured-template contract
 -> v715 structured-template corpus materialization
 -> v716 real tiny training + heldout direct replay
```

v716 沿用 v707/v712 的训练配置，保证对比边界一致：

```text
seed=3535
max_iters=1400
batch_size=16
block_size=16
n_layer=1
n_head=1
n_embd=64
learning_rate=0.02
temperature=0.2
top_k=1
device=cpu
```

## 输入输出

输入：

```text
e/715/解释/model-capability-required-term-pair-readiness-structured-template-corpus-materialization/
```

核心输出：

- `model_capability_required_term_pair_readiness_training_run.json`
  - 训练与 replay 的主报告。

- `pair-readiness-training-run/checkpoint.pt`
  - 真实 tiny checkpoint。

- `pair-readiness-training-run/tokenizer.json`
  - 本次训练使用的 tokenizer。

- `pair-readiness-training-run/metrics.jsonl`
  - 训练 metrics。

- `heldout-direct-replay/`
  - fixed/loss heldout direct replay 产物。

## 结果摘要

v716 输出：

```text
status=pass
decision=pair_readiness_training_no_pair_full
training_status=pass
checkpoint_exists=True
pair_full_observed=False
default_continuation_hit_count=1
model_quality_claim=not_claimed
```

replay variants 显示：

```text
default: hit_terms=['loss'], missed_terms=['fixed'], pair_full=False
suppress_newline_tokens: hit_terms=['loss'], missed_terms=['fixed'], pair_full=False
```

这和 v707/v712 不同：

- v707 命中 `fixed`，miss `loss`。
- v712 两边都没有稳定完整命中。
- v716 命中 `loss`，miss `fixed`。

## 工程意义

v716 的价值不是“能力提升”，而是把失败形态变得更清楚：

- prefix-only loss-retention route 会过度强化 `los`，使两边都坏掉。
- structured-template route 能恢复 `loss`，但牺牲 `fixed`。
- 当前 tiny 模型仍没有在 minimal/direct prompt 下学到稳定双分支。

这说明下一步应该做比较或诊断，而不是立刻继续扩写 corpus。

## 测试与验证

本版没有新增代码，但继承 v715 的 materializer locator 修复和 training run 链路。

运行证据：

- `e/716/图片/v716-structured-template-training-run.png`
- `e/716/解释/model-capability-required-term-pair-readiness-structured-template-training-run/`

截图中可以看到：

```text
Pair-full=False
Claim=not_claimed
hit_terms=['loss']
missed_terms=['fixed']
```

## 一句话总结

v716 用真实 tiny training 证明 structured-template route 仍未达到 pair-full，但它把失败从 fixed-dominant 转成 loss-only，为下一版比较诊断提供了新证据。
