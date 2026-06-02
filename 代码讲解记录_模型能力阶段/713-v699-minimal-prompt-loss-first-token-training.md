# v699 minimal prompt loss first-token training

## 本版目标和边界

v699 是 v698 repair plan 的真实训练执行版。它使用 `minimal_prompt_loss_first_token_repair_objective`，同 seed `3535`，与 v696 形成直接对照。

本版不做 promotion。即使命中了 loss，也不能只看单边结果，因为目标是 fixed 和 loss 同时 pair-full。

## 前置链路

v696：

```text
fixed= -> fixed=fixed=fixed=
loss=  -> loss=fixed=fixed=
```

v697：

```text
decision=minimal_prompt_branch_bias_fixed_absorbs_loss
dominant_bias=fixed
```

v698：

```text
proposed_corpus_mode=minimal_prompt_loss_first_token_repair_objective
```

v699 执行这个 proposed corpus mode。

## 运行设置

- `seed=3535`
- `corpus_mode=minimal_prompt_loss_first_token_repair_objective`
- `repeat=260`
- `bridge_repeat=20`
- `max_iters=1400`
- `n_embd=64`
- `top_k=1`
- `temperature=0.2`

这些设置与 v696 保持一致，主要变量是 corpus mode。

## 结果解释

报告结论：

```text
decision=required_term_pair_coexistence_refresh_no_pair_full
pair_full_observed=False
model_quality_claim=not_claimed
```

case rows 显示：

```text
fixed= -> losssssss= l
loss=  ->  losssssss=
```

与 v696 相比：

- v696 的 `fixed=` 成功，`loss=` 失败。
- v699 的 `loss=` 成功，`fixed=` 失败。

这不是完全失败，而是偏置从 fixed-dominant 变成 loss-dominant。

## 为什么重要

v699 证明 v698 的 loss-first-token 修复确实影响了模型输出分布。但它也说明单边增强会破坏另一条分支。下一步应该比较两份真实训练报告，寻找平衡策略，而不是继续堆 loss rows。

## 运行证据

证据目录：

```text
e/699/解释/model-capability-required-term-pair-minimal-prompt-loss-first-token-training/
e/699/图片/v699-minimal-prompt-loss-first-token-training.png
```

主要产物包括 checkpoint、tokenizer、metrics、corpus 和 replay report。

## 下一步

v700 应比较 v696/v699：

- 哪个 term 命中。
- 哪个 term 被竞争分支吸走。
- 是否存在 pair-full。
- 下一版应做 balanced repair，而不是继续单边 loss 或 fixed。

## 一句话总结

v699 把 minimal-prompt 失败从 fixed-dominant 推成 loss-dominant，证明修复有作用但仍缺分支平衡。
