# v544 required-term pair top-k2 t0.8 stability 代码讲解

## 本版目标和边界

v543 发现 `topk2-t080-n12` 能在 v542 checkpoint 上把 pair-full 从 `1/3` 提升到 `2/3`。v544 用正式 colon-immediate stability runner 复验这个配置，确认它不是单独 decode-boundary 报告里的偶然结果。

本版不新增代码，不改训练 corpus，不改模型结构。唯一实验变化是 replay 解码参数：

```text
top_k=2
temperature=0.8
max_new_tokens=12
```

## 前置能力

v544 复用：

- v543 新增的自定义 decode spec 结论。
- v542 已验证的 high-budget colon-immediate stability 参数。
- 既有 missed-seed diagnostic，用于定位未恢复 seed 的 first-token 形态。

## 输入参数

训练侧保持 v540/v542 一致：

```text
corpus_mode=colon_immediate
seeds=535,1535,2535
repeat=420
bridge_repeat=40
max_iters=2200
n_layer=1
n_head=1
n_embd=64
learning_rate=0.02
```

解码侧使用 v543 最佳配置：

```text
top_k=2
temperature=0.8
max_new_tokens=12
```

## 关键产物

- `e/544/解释/model-capability-required-term-pair-topk2-t080-stability/`
  - 三 seed 训练、checkpoint、replay、stability JSON/CSV/HTML。
- `e/544/解释/model-capability-required-term-pair-topk2-t080-missed-seed-diagnostic/`
  - 对 v544 stability 的 first-token 诊断。
- `e/544/图片/`
  - Playwright MCP 截图，证明两份 HTML 报告可读。

## 真实结果

stability：

```text
decision=required_term_pair_colon_immediate_partial_stability
pair_full_seed_count=2/3
```

seed 明细：

```text
535  -> pair_full=True
1535 -> pair_full=False
2535 -> pair_full=True
```

diagnostic：

```text
missed_seed_count=1
missed_first_token_gap_count=1
```

seed `1535` 的 fixed/loss ranks 为 `1/2`，但生成仍没有覆盖 pair-full，说明它是下一步最值得定向修复的样本。

## 链路角色

v544 是一个收口型实验版：它把 v543 的温度边界发现从“离线 replay 观察”提升为“正式 stability 证据”。这使后续路线更清楚：不是继续盲目扩大训练预算，而是围绕 seed `1535` 的 first-token 和 sampling 行为做定向数据修复。

## 验证覆盖

验证包括：

- 真实三 seed 训练和 replay。
- stability JSON/CSV/text/Markdown/HTML 产物。
- missed-seed diagnostic JSON/CSV/text/Markdown/HTML 产物。
- Playwright MCP 截图和 snapshot。
- 全量 pytest、source encoding、`git diff --check` 和 GitHub Actions。

一句话总结：v544 证明 `top_k=2, temperature=0.8` 是当前 fixed/loss pair 的最佳正式稳定性配置，但仍只达到 `2/3`。
