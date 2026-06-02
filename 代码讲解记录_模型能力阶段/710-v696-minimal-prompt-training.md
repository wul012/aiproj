# v696 minimal prompt training

## 本版目标和边界

v696 是 minimal-prompt 目标的第一次真实 tiny 训练。它使用 v695 验证过的 `minimal_prompt_equals_surface_objective` corpus mode，训练 seed `3535`，再用 generation profile replay 检查 `fixed=` / `loss=` 两个最小提示词。

本版不做 promotion，不扩大模型规模，不把局部命中包装成 pair-full。它只回答：v695 的无 contextual anchor 语料，能不能让 tiny 模型在最小提示词下同时生成 fixed 和 loss。

## 前置链路

v694 证明路线可以开启：

```text
minimal_prompt_surface_objective_ready_for_corpus_contract
```

v695 证明语料契约可用：

```text
minimal_prompt_equals_surface_corpus_contract_ready
```

v696 在这个基础上首次执行真实训练。

## 关键输入

训练命令使用：

- `seed=3535`
- `corpus_mode=minimal_prompt_equals_surface_objective`
- `repeat=260`
- `bridge_repeat=20`
- `max_iters=1400`
- `batch_size=16`
- `block_size=16`
- `n_layer=1`
- `n_head=1`
- `n_embd=64`
- `learning_rate=0.02`
- `top_k=1`
- `temperature=0.2`

这是保持 tiny 规模的 targeted training，不是生产级大模型训练。

## 关键产物

主报告：

```text
e/696/解释/model-capability-required-term-pair-minimal-prompt-training/model_capability_required_term_pair_coexistence_refresh.json
```

训练产物：

```text
pair-coexistence-refresh-run/checkpoint.pt
pair-coexistence-refresh-run/tokenizer.json
pair-coexistence-refresh-run/metrics.jsonl
pair-coexistence-refresh-run/train_config.json
```

replay 产物：

```text
pair-generation-profile-replay/model_capability_required_term_pair_generation_profile_replay.json
```

这些产物共同证明：训练链路完成，生成链路完成，失败来自模型输出而不是脚本中断。

## 输出结果解释

报告顶部结论：

```text
status=pass
decision=required_term_pair_coexistence_refresh_no_pair_full
training_status=pass
checkpoint_exists=True
pair_full_observed=False
model_quality_claim=not_claimed
```

这说明：

- 训练执行成功。
- checkpoint 真实存在。
- replay 正常执行。
- 但 fixed/loss 没有同时命中。

关键 case rows 显示：

```text
fixed= -> fixed=fixed=fixed=
loss=  -> loss=fixed=fixed=
```

因此 v696 的失败点很明确：`fixed=` 分支可被学到，`loss=` 分支在最小提示词下被 fixed 分支吸走。

## 为什么这是有价值的负证据

v696 不是“无结果”。它证明了三件事：

1. v695 的语料可以驱动真实训练流程。
2. tiny 模型不是完全不会生成 required term，因为 fixed 命中。
3. 当前 objective 对 loss 分支的 first-token 或 branch separation 约束仍不足。

这比继续堆 contextual variants 更接近真实模型能力问题。

## 测试和验证

v696 沿用 v695 已通过的 corpus contract tests。运行侧验证来自真实 CLI：

```powershell
python -B scripts\run_model_capability_required_term_pair_coexistence_refresh.py ...
```

命令返回 `0`，且 `training_status=pass`、`checkpoint_exists=True`。这证明失败不是执行失败，而是能力未达标。

## 运行证据

运行截图：

```text
e/696/图片/v696-minimal-prompt-training.png
```

说明文件：

```text
e/696/解释/说明.md
```

## 下一步

下一版最合理的是做 first-token / branch-bias diagnostic：

- 看 `loss=` 第一个生成 token 是否已经偏向 `f`。
- 对比 default 和 suppression profile。
- 判断应该修 loss 首 token，还是需要更强 branch separation。

## 一句话总结

v696 用真实 tiny 训练证明 minimal-prompt 路线第一次尝试仍未 pair-full，失败集中在 `loss=` 被固定吸向 `fixed`。
