# v894 bounded objective loss signal bridge target-only memory decoder budget audit

## 本版目标和边界

v894 的目标是解释 v891 replay 为什么只输出 `\nfixed l`。v893 已经证明在 `prompt + "\nfixed l"` 后，目标 `oss` 的三个 token 在所有 contract case 中都是 top-1。因此，下一步不是继续补训练数据，而是检查 replay 的生成预算是否太短。

本版明确不做：

- 不重新训练。
- 不重新 replay。
- 不修改 v891 历史证据。
- 不把预算解释当作 contract pass。

它只读取 v891 replay、v893 probability probe 和 v890 tokenizer，计算 continuation token count、剩余预算和补齐 `oss` 需要的 token 数。

## 前置能力

本版承接：

- v891：真实 replay 结果是三条 `\nfixed l` partial。
- v893：`fixed l` 后的 `o/s/s` 全部是 top-1。
- 现有 replay 比较层：默认 `GenerationRequest(max_new_tokens=8, temperature=0.2, top_k=20, seed=1839)`。

v894 把这三件事连起来，判断 v891 是“模型不会”，还是“预算不给继续生成”。

## 关键文件

`src/minigpt/bounded_objective_loss_signal_bridge_target_only_memory_decoder_budget_audit.py`

核心审计模块。它读取 replay rows 和 probability probe case rows，用 tokenizer 计算 token 数，并生成 `case_rows`、`diagnostic`、`summary`。

`src/minigpt/bounded_objective_loss_signal_bridge_target_only_memory_decoder_budget_audit_artifacts.py`

输出层。它把审计结果写成 JSON、CSV、TXT、Markdown 和 HTML。CSV 保留每个 case 的预算字段。

`scripts/audit_bounded_objective_loss_signal_bridge_target_only_memory_decoder_budget.py`

CLI 入口。输入 replay comparison、loss-token probability probe 和 tokenizer，输出审计 artifact。

`tests/test_bounded_objective_loss_signal_bridge_target_only_memory_decoder_budget_audit.py`

测试文件。它验证预算耗尽路径、预算已经足够时的失败路径、probability probe 非 top-1 时的失败路径，以及 CLI 输出。

## 核心数据结构

`case_rows` 是本版最重要的结构。每条 case 包含：

- `continuation`：v891 replay continuation。
- `continuation_token_count`：continuation 用掉的新 token 数。
- `max_new_tokens`：v891 replay 的生成预算。
- `remaining_budget`：剩余可生成 token 数。
- `target_suffix`：缺失的后缀，本版是 `oss`。
- `target_suffix_token_count`：补齐后缀需要的 token 数。
- `needed_max_new_tokens`：当前 continuation 加缺失后缀需要的总预算。
- `additional_tokens_needed`：当前预算还差多少。
- `loss_suffix_top1`：来自 v893 的概率证据。
- `budget_exhausted_before_suffix`：是否预算已经耗尽但还有 top-1 后缀没生成。

`diagnostic` 聚合这些 case：

- `budget_exhausted_case_count`
- `loss_suffix_top1_case_count`
- `all_cases_budget_exhausted_before_top1_suffix`
- `recommended_max_new_tokens`
- `max_additional_tokens_needed`
- `next_step`

## 核心函数

`build_decoder_budget_audit()`

总入口。它加载 tokenizer，读取 replay summary 和 probability summary，构建 case rows，再运行 checks。

`_case_rows()`

对每条 replay row 计算：

```text
remaining_budget = max_new_tokens - continuation_token_count
needed_max_new_tokens = continuation_token_count + target_suffix_token_count
additional_tokens_needed = needed_max_new_tokens - max_new_tokens
```

真实 v891 中，`\nfixed l` 是 8 个 char token，`max_new_tokens` 也是 8，所以剩余预算为 0。

`_diagnostic()`

如果所有 case 都满足“预算耗尽 + suffix top-1”，就把下一步设置为 `rerun_stagnation_aware_suffix_replay_with_max_new_tokens_11`。

## 本版真实结果

真实运行结果：

```text
status=pass
decision=bounded_objective_loss_signal_bridge_target_only_memory_decoder_budget_exhausted_before_loss_suffix
budget_exhausted_case_count=3
loss_suffix_top1_case_count=3
recommended_max_new_tokens=11
max_additional_tokens_needed=3
```

逐 case 结论一致：

```text
continuation_token_count=8
max_new_tokens=8
remaining_budget=0
target_suffix=oss
target_suffix_token_count=3
needed_max_new_tokens=11
```

这说明 v891 的 `loss` miss 不能简单解释成模型不会生成 `loss`。更精确地说，它生成到 `fixed l` 时预算已经用完，而 v893 证明继续生成 `oss` 的概率很高。

## 测试覆盖

测试覆盖：

- 三条 case 都预算耗尽且 suffix top-1 时，audit 必须 pass。
- 如果 `max_new_tokens=11` 已经足够但仍只输出 `fixed l`，audit 不能继续声称预算耗尽，必须 fail。
- 如果 v893 probability probe 不是 top-1，audit 也不能把问题归因给预算。
- CLI 可以从目录定位 replay/probe JSON，并写出五类 artifact。

## 运行证据

运行证据保存在：

- `e/894/解释/说明.md`
- `e/894/解释/bounded-objective-loss-signal-bridge-target-only-memory-decoder-budget-audit/`
- `e/894/图片/v894-bounded-objective-loss-signal-bridge-target-only-memory-decoder-budget-audit-html.png`

截图证明 HTML artifact 可打开，并展示 `budget_exhausted_case_count=3`、`recommended_max_new_tokens=11` 和下一步重跑 replay 的路线。

## 一句话总结

v894 把 v891 的 replay miss 从“模型没学会”定位为“8 token 解码预算卡住了 top-1 的 oss 后缀”，下一版应使用 11 token 预算重新 replay。
