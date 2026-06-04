# v863：bounded objective loss signal bridge partial-hit diagnostic

## 本版目标和边界

v863 的目标是解释 v862 的 partial-hit 结果。v862 已经证明 v861 checkpoint 在三个 bounded objective contract cases 上没有任何完整通过，但有两个 case 命中了一个 required term。

这类结果不能简单说“模型失败”，也不能简单说“模型变好了”。它需要拆成更具体的问题：是两个词都没学到，还是两个词分别学到了但没有绑定成 `fixed loss`。

边界：

- 不训练。
- 不重新 replay。
- 不修改 v836 contract。
- 不使用 decoder anchor。
- 不把 partial hit 当作 promotion 信号。

## 前置链路

```text
v860 loss signal bridge corpus
 -> v861 loss signal bridge training run
 -> v862 loss signal bridge replay comparison
 -> v863 partial-hit diagnostic
```

v863 的职责是从 v862 的 replay rows 里提取原因，给下一版数据补丁提供证据。

## 关键新增文件

- `src/minigpt/bounded_objective_loss_signal_bridge_partial_hit_diagnostic.py`
  - 读取 v862 replay comparison。
  - 按 case 分类 `fixed_only`、`loss_only`、`zero_hit`、`pair_pass`。
  - 生成 root causes 和下一步建议。

- `src/minigpt/bounded_objective_loss_signal_bridge_partial_hit_diagnostic_artifacts.py`
  - 输出 JSON、CSV、TXT、Markdown、HTML。
  - HTML 展示 case diagnostics 和 root causes。

- `scripts/diagnose_bounded_objective_loss_signal_bridge_partial_hit.py`
  - CLI 入口。
  - 支持 `--replay-comparison`、`--out-dir`、`--require-diagnostic-ready`、`--force`。

- `tests/test_bounded_objective_loss_signal_bridge_partial_hit_diagnostic.py`
  - 覆盖 pair-binding gap、无 partial hit 阻断、writer 和 CLI。

- `e/863/解释/bounded-objective-loss-signal-bridge-partial-hit-diagnostic/`
  - v863 真实诊断证据。

- `e/863/图片/v863-bounded-objective-loss-signal-bridge-partial-hit-diagnostic-html.png`
  - Playwright MCP 截图。

## 核心输入

v863 输入 v862 的 replay comparison：

```text
summary.bounded_objective_loss_signal_bridge_replay_comparison_ready
summary.objective_contract_recovered
summary.passed_case_count
summary.any_hit_case_count
summary.zero_hit_case_count
replay_rows[]
loss_signal_bridge_training_summary
```

其中最重要的是每个 replay row：

```text
case_id
continuation
hit_terms
missed_terms
case_pass
any_hit
max_new_tokens
```

v863 不需要再读 checkpoint，也不需要再生成文本。它只读 v862 已经冻结的 replay evidence。

## Case 分类规则

`_case_diagnostic()` 会给每一行打标签：

```text
pair_pass   -> case_pass=True
fixed_only  -> hit_terms 包含 fixed，但不包含 loss
loss_only   -> hit_terms 包含 loss，但不包含 fixed
other_partial -> 有命中，但不是固定两类
zero_hit    -> 没有任何 required-term 命中
```

同时它记录：

```text
has_fixed_fragment
has_loss_fragment
continuation_len
max_new_tokens
```

这些字段用于判断模型是否只是输出了短片段，而不是稳定输出目标 pair。

## Root cause 规则

v863 生成的 root causes 包括：

```text
paired_term_binding_gap
completion_surface_zero_hit
fragmented_required_term_surface
no_anchor_partial_signal
```

其中最关键的是：

```text
paired_term_binding_gap
```

触发条件是：

```text
fixed_only_case_count > 0
loss_only_case_count > 0
passed_case_count == 0
```

也就是说，模型分别能碰到 `fixed` 和 `loss`，但没有任何 case 把它们绑定成完整 `fixed loss`。

## 真实诊断结果

命令：

```text
python -B scripts/diagnose_bounded_objective_loss_signal_bridge_partial_hit.py
  --replay-comparison e/862/解释/bounded-objective-loss-signal-bridge-replay-comparison
  --out-dir e/863/解释/bounded-objective-loss-signal-bridge-partial-hit-diagnostic
  --require-diagnostic-ready
  --force
```

输出：

```text
status=pass
decision=bounded_objective_loss_signal_bridge_partial_hit_pair_binding_gap
partial_case_count=2
fixed_only_case_count=1
loss_only_case_count=1
zero_hit_case_count=1
paired_signal_split=True
model_quality_claim=partial_signal_split_without_pair_binding
```

case 级别：

```text
canonical_direct_completion -> loss_only
minimal_direct_completion   -> fixed_only
completion_label_surface    -> zero_hit
```

这比“再训练一版看看”更有价值，因为它指出下一版训练数据应该强化 pair binding，而不是继续笼统增加样本。

## 下一步为什么是 pair-binding patch

v860 的 bridge corpus 已经让 `fixed` 和 `loss` 都能局部出现。v862/v863 说明问题卡在两个点：

- 目标词没有稳定连续出现。
- completion surface 仍然可能完全丢失两个词。

所以 v864 更合理的方向是：

```text
build_bounded_objective_loss_signal_bridge_pair_binding_patch
```

这个 patch 应该围绕同一 prompt surface 重复强化：

```text
fixed loss
completion: fixed loss
answer: fixed loss
exactly two tokens: fixed loss
```

同时继续保持：

```text
decoder_anchor=False
promotion_ready=False
```

## 测试覆盖

focused pytest 覆盖：

- pair-binding gap：
  - 一个 `loss_only`，一个 `fixed_only`，一个 `zero_hit`。
  - 诊断必须 ready，并输出 `paired_term_binding_gap`。

- no partial hit：
  - `any_hit_case_count=0` 且无 replay rows。
  - 诊断必须 fail，避免误用。

- writer + CLI：
  - locate、JSON/CSV/TXT/Markdown/HTML 输出和 CLI wiring。

```text
3 passed
```

## 运行证据

产物：

```text
e/863/解释/bounded-objective-loss-signal-bridge-partial-hit-diagnostic/
```

截图：

```text
e/863/图片/v863-bounded-objective-loss-signal-bridge-partial-hit-diagnostic-html.png
```

Playwright MCP snapshot 确认页面展示：

```text
Status=pass
Decision=bounded_objective_loss_signal_bridge_partial_hit_pair_binding_gap
Pair split=True
Partial=2
Fixed only=1
Loss only=1
Zero hit=1
Claim=partial_signal_split_without_pair_binding
```

## 一句话总结

v863 把 v862 的 partial hit 从“现象”推进成“原因”：模型有无锚点局部信号，但缺少 `fixed loss` 的有序 pair binding。
