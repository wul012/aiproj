# v542 required-term pair top-k2 stability 代码讲解

## 本版目标和边界

v541 通过 decode boundary check 发现 `wider-k2-t020-n12` 可以让 v540 的 seed `535` 恢复 pair-full。v542 不写新模块，而是把这个解码边界放回已有 colon-immediate stability runner，做一次正式三 seed 复验。

本版只改变 replay 解码参数 `top_k=2`，不改变训练 corpus、模型结构、训练预算或 seed 组。

## 前置能力

v542 复用两条已有能力：

- `scripts/run_model_capability_required_term_pair_colon_immediate_stability.py`
  - 已支持 `--top-k`、`--temperature`、`--max-new-tokens`。
- `scripts/run_model_capability_required_term_pair_colon_immediate_missed_seed_diagnostic.py`
  - 对未命中的 seed 做 first-token logits 诊断。

因此本版是受控实验版本，不需要新增代码文件。

## 输入参数

与 v540 保持一致：

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

唯一关键变化：

```text
top_k: 1 -> 2
```

## 关键产物

- `e/542/解释/model-capability-required-term-pair-topk2-stability/`
  - 三 seed 训练、checkpoint、replay、stability JSON/CSV/HTML。
- `e/542/解释/model-capability-required-term-pair-topk2-missed-seed-diagnostic/`
  - 对 top-k2 stability report 的 first-token 诊断。
- `e/542/图片/`
  - 两张 Playwright MCP 截图，分别证明 stability 和 missed-seed diagnostic 可读。

这些产物是最终运行证据，不是临时调试文件。

## 真实结果

stability：

```text
decision=required_term_pair_colon_immediate_partial_stability
pair_full_seed_count=1/3
```

seed 明细：

```text
535  -> pair_full=True
1535 -> pair_full=False
2535 -> pair_full=False
```

missed-seed diagnostic：

```text
decision=required_term_pair_colon_immediate_first_token_gap
missed_seed_count=2
missed_first_token_gap_count=2
```

这说明 `top_k=2` 能复现 v541 发现的 seed `535` 恢复，但另外两个 seed 的第一 token 偏置仍没解决。

## 链路角色

v542 的角色是把 v541 的“离线 decode boundary 观察”升级为“正式 stability 运行证据”。它避免了直接切回训练数据前遗漏一个重要事实：当前模型并非完全没有 fixed/loss pair 信号，至少一个 seed 的信号可以通过更宽的解码边界表达出来。

## 验证覆盖

验证重点是：

- 真实 PyTorch 三 seed 训练全部完成。
- 三个 seed 都生成 checkpoint/tokenizer。
- stability report 正常写出 JSON/CSV/text/Markdown/HTML。
- missed-seed diagnostic 能读取 v542 stability report 并完成 first-token logits 检查。
- Playwright MCP 能打开两份 HTML 并保存截图。
- 后续全量测试、source encoding 和 `git diff --check` 会继续作为版本门禁。

一句话总结：v542 证明 `top_k=2` 是有效但不足的解码补偿，下一步仍要修 first-token preference。
