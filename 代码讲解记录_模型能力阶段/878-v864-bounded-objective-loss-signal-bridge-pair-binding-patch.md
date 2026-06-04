# v864：bounded objective loss signal bridge pair-binding patch

## 本版目标和边界

v864 的目标是把 v863 的诊断结论转成可训练数据。v863 已经说明 v862 的问题不是完全没有 `fixed` 或 `loss`，而是两个词分别出现在不同 case 中，没有稳定绑定成 `fixed loss`。

v864 因此构建 pair-binding patch：围绕 v862 失败 replay rows 的原始 prompt surface，生成 no-anchor 的 JSONL 和 corpus。

边界：

- 不训练。
- 不 replay。
- 不 promotion。
- 不使用 decoder anchor。
- 不 claim 模型能力提升。

## 前置链路

```text
v862 replay comparison
 -> v863 partial-hit diagnostic
 -> v864 pair-binding patch
```

v864 不是新的治理链，而是对 v863 明确诊断的落实：既然问题是 pair binding，就生成 pair-binding 训练样本。

## 关键新增文件

- `src/minigpt/bounded_objective_loss_signal_bridge_pair_binding_patch.py`
  - 核心 patch builder。
  - 输入 v863 diagnostic、v862 replay comparison 和 v861 prepared corpus。
  - 从 replay rows 读取原始 prompt surface。
  - 输出 patch examples 和 patched corpus。

- `src/minigpt/bounded_objective_loss_signal_bridge_pair_binding_patch_artifacts.py`
  - 输出 JSON、CSV、JSONL、corpus、TXT、Markdown、HTML。

- `scripts/build_bounded_objective_loss_signal_bridge_pair_binding_patch.py`
  - CLI 入口。
  - 支持 `--partial-hit-diagnostic`、`--replay-comparison`、`--source-corpus`、`--out-dir`、`--require-patch-ready`、`--force`。

- `tests/test_bounded_objective_loss_signal_bridge_pair_binding_patch.py`
  - 覆盖 patch ready、无 pair split 阻断、writer 和 CLI。

- `e/864/解释/bounded-objective-loss-signal-bridge-pair-binding-patch/`
  - v864 真实 patch 证据。

- `e/864/图片/v864-bounded-objective-loss-signal-bridge-pair-binding-patch-html.png`
  - Playwright MCP 截图。

## 输入数据

v864 读取三类输入。

第一类是 v863 diagnostic：

```text
summary.bounded_objective_loss_signal_bridge_partial_hit_diagnostic_ready
summary.paired_signal_split
case_diagnostics[].case_id
case_diagnostics[].label
```

第二类是 v862 replay：

```text
summary.bounded_objective_loss_signal_bridge_replay_comparison_ready
summary.objective_contract_recovered
replay_rows[].case_id
replay_rows[].prompt
```

第三类是 v861 prepared corpus：

```text
e/861/解释/bounded-objective-loss-signal-bridge-training-run/run/prepared_corpus.txt
```

v864 把新样本追加到这个 corpus 后面，得到新的 patched corpus。

## Patch 生成规则

对于每个 case，先生成两条：

```text
case_pair_repeat
```

也就是在原始失败 prompt 后直接重复：

```text
fixed loss
```

然后根据 v863 label 增加定向样本。

如果是 `fixed_only`：

```text
fixed_to_loss_binding
fixed_to_pair_binding
```

目的：让 `fixed` 后面稳定接 `loss`。

如果是 `loss_only`：

```text
loss_to_pair_binding
loss_left_context_binding
```

目的：让 `loss` 回到 `fixed loss` 的完整 pair。

如果是 `zero_hit`：

```text
completion_surface_pair_repair
```

目的：修复 completion surface 下两个词都丢失的问题。

最后补充全局短样本：

```text
global_pair_binding
global_pair_repeat
```

它们强化最短形式：

```text
fixed -> loss
answer: -> fixed loss
completion: -> fixed loss
target: -> fixed loss
```

## 真实结果

命令：

```text
python -B scripts/build_bounded_objective_loss_signal_bridge_pair_binding_patch.py
  --partial-hit-diagnostic e/863/解释/bounded-objective-loss-signal-bridge-partial-hit-diagnostic
  --replay-comparison e/862/解释/bounded-objective-loss-signal-bridge-replay-comparison
  --source-corpus e/861/解释/bounded-objective-loss-signal-bridge-training-run/run/prepared_corpus.txt
  --out-dir e/864/解释/bounded-objective-loss-signal-bridge-pair-binding-patch
  --require-patch-ready
  --force
```

输出：

```text
status=pass
decision=bounded_objective_loss_signal_bridge_pair_binding_patch_ready
patch_example_count=18
case_pair_repeat_count=6
pair_binding_example_count=6
completion_surface_example_count=2
decoder_anchor_example_count=0
patched_corpus_char_count=4771
model_quality_claim=pair_binding_patch_only
```

## 为什么还是不能 claim 能力

v864 只是数据补丁：

```text
pair_binding_patch_only
```

它还没有经过：

```text
training run
replay comparison
holdout replay
```

所以本版只能说明“下一次训练输入更对准 pair-binding gap”，不能说明模型已经恢复 contract。

## 测试覆盖

focused pytest 覆盖：

- pair-binding patch ready：
  - diagnostic ready。
  - paired signal split 为 true。
  - replay ready 且 contract not recovered。
  - 生成 JSONL 和 corpus。

- 无 pair split 阻断：
  - `paired_signal_split=False` 时必须 fail。

- writer + CLI：
  - locate、JSON/CSV/JSONL/corpus/TXT/Markdown/HTML 输出和 CLI wiring。

```text
3 passed
```

## 运行证据

产物：

```text
e/864/解释/bounded-objective-loss-signal-bridge-pair-binding-patch/
```

截图：

```text
e/864/图片/v864-bounded-objective-loss-signal-bridge-pair-binding-patch-html.png
```

Playwright MCP snapshot 确认页面展示：

```text
Status=pass
Decision=bounded_objective_loss_signal_bridge_pair_binding_patch_ready
Examples=18
Pair binding=6
Completion surface=2
Anchors=0
Claim=pair_binding_patch_only
```

## 一句话总结

v864 把“fixed/loss 分裂”转化为可训练的 no-anchor pair-binding patch，为下一版真实训练提供更精准的数据输入。
