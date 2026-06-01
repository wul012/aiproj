# v606 required-term pair fixed-retention loss-rebalance seed 3535

## 本版目标和边界

v606 承接 v605 的 loss-rebalance corpus mode，跑一次真实 tiny 训练，检查它是否能同时保留 fixed branch 和 loss branch。

本版只验证一个具体语料路线，不新增语料设计，不改变模型结构，也不把负结果包装成模型能力提升。

## 前置链路

```text
v603 comparison: 三条 fixed-retention 路线都没有 pair-full
v604 route decision: 选择 v601 first-token 作为 fixed recovery evidence
v605 corpus: 在 fixed first-token rows 基础上补 loss rows
v606 training: 用 loss-rebalance mode 跑真实 seed 3535
```

这条链路的关键问题是：v601 能恢复 `fixed=`，但会丢 `loss=`；v605 试图补回 loss；v606 检查补回后是否仍能保住 fixed。

## 关键产物

```text
e/606/解释/model-capability-required-term-pair-fixed-retention-loss-rebalance-seed-3535/
e/606/图片/v606-fixed-retention-loss-rebalance-seed-3535.png
e/606/解释/说明.md
```

`model_capability_required_term_pair_coexistence_refresh.json` 是本版的机器可读证据，记录训练状态、checkpoint 是否存在、replay rows、pair-full 判定和下一步建议。

HTML/Markdown/text 是同一份证据的浏览和归档版本；截图只证明 HTML 报告可打开，不替代 JSON。

## 输入输出

输入命令使用 v605 模式：

```text
--corpus-mode equals_surface_no_pair_id_fixed_retention_loss_rebalance_repair
--seed 3535
--max-iters 1800
--n-embd 64
--temperature 0.2
--top-k 1
```

输出结果：

```text
status=pass
decision=required_term_pair_coexistence_refresh_no_pair_full
training_status=pass
checkpoint_exists=True
pair_full_observed=False
```

Replay rows 显示：

```text
fixed= -> lossssssssss
loss=  -> lossssssssss
```

因此本版没有达到 pair-full；它把目标从 v601 的 fixed-only 迁移成 loss-only。

## 测试和证据覆盖

本版复用 `run_model_capability_required_term_pair_coexistence_refresh.py` 的训练、生成和 replay 判定链路：

- 训练命令真实生成 checkpoint 和 tokenizer。
- replay 检查 default 与 newline-suppression 两个 profile。
- `--require-pass` 只要求流程通过，不要求 pair-full；这保证负结果也能被归档。
- Playwright MCP 打开 HTML 报告并截图，确认归档报告可读。

## 一句话总结

v606 证明 loss-rebalance route 仍是 branch tradeoff：它恢复 loss，但没能保住 fixed。
