# v860：bounded objective loss signal bridge

## 本版目标和边界

v860 的目标是把 v859 profile sweep 里观察到的 `loss` signal 转成新的训练数据。

v859 已经证明：某些 profile 可以生成 `loss`，但生成 `loss` 的时候往往 missed `fixed`；生成 `fixed` 的 profile 又 missed `loss`。v860 不继续调参，而是把这两个单侧信号桥接成 `fixed loss` 共现样本。

边界：

- 不训练。
- 不 replay checkpoint。
- 不修改 bounded objective contract。
- 不把 bridge corpus 当作模型能力。
- 不使用 decoder anchor。

## 前置链路

```text
v858 shape migration diagnostic
 -> v859 curriculum patch profile sweep
 -> v860 loss signal bridge
```

v859 的 next action 是：

```text
build_loss_signal_bridge_without_promotion
```

v860 正是这个无 promotion 的桥接数据版本。

## 关键新增文件

- `src/minigpt/bounded_objective_loss_signal_bridge.py`
  - v860 builder。读取 profile sweep 和 source corpus，生成 bridge examples 与 bridged corpus。
- `src/minigpt/bounded_objective_loss_signal_bridge_artifacts.py`
  - 输出 JSON/CSV/JSONL/corpus/TXT/Markdown/HTML。
- `scripts/build_bounded_objective_loss_signal_bridge.py`
  - CLI 入口。
- `tests/test_bounded_objective_loss_signal_bridge.py`
  - 覆盖 loss signal bridge、无 loss signal 阻断、writer 和 CLI。
- `e/860/解释/bounded-objective-loss-signal-bridge/`
  - 保存真实 bridge 产物。
- `e/860/图片/v860-bounded-objective-loss-signal-bridge-html.png`
  - Playwright MCP 截图。

## 核心数据结构

每条 `bridge_examples` 包含：

```text
example_id
kind
prompt
completion
text
required_terms
decoder_anchor
source_profile_id
source_case_id
source_continuation
purpose
```

核心 `kind`：

- `loss_signal_pair_bridge`
  - 从 loss-only 行生成 `fixed loss` completion。
- `loss_signal_prefix_repair`
  - 在 prompt 后显式接入 `loss` prefix，再要求回到 `fixed loss`。
- `fixed_signal_pair_bridge`
  - 从 fixed-only 行补齐 `fixed loss`。
- `pair_reinforcement`
  - 直接强化目标 pair。

## 核心流程

`build_bounded_objective_loss_signal_bridge()` 做五步：

1. 读取 v859 `sweep_rows`。
2. 选出 `loss_hit=True and fixed_hit=False` 的 loss-only 行。
3. 选出 `fixed_hit=True and loss_hit=False` 的 fixed-only 行。
4. 生成 bridge examples。
5. 把 examples 追加到 v855 patched corpus，形成 v860 bridged corpus。

检查条件：

```text
profile_sweep_passed
profile_sweep_ready
loss_signal_present
contract_not_recovered
sweep_rows_present
bridge_examples_present
decoder_anchor_free
```

如果 profile sweep 已经恢复 contract，v860 会阻断，因为那时应该做 holdout，而不是继续做 bridge。

## 真实结果

```text
status=pass
decision=bounded_objective_loss_signal_bridge_ready
bridge_example_count=16
loss_signal_bridge_example_count=6
fixed_signal_bridge_example_count=6
pair_reinforcement_example_count=4
bridged_corpus_char_count=3908
model_quality_claim=bridge_corpus_only
next_step=train_bounded_objective_loss_signal_bridge
```

## 产物角色

JSON 是主证据，记录输入 summary、source signal summary、bridge examples 和 checks。

JSONL 是后续训练可消费的样本表。

Corpus 是下一版训练输入：

```text
e/860/解释/bounded-objective-loss-signal-bridge/bounded_objective_loss_signal_bridge_corpus.txt
```

HTML/Markdown/TXT 是人读证据，不直接作为训练输入。

## 测试覆盖

focused pytest 覆盖：

- 有 loss-only 和 fixed-only 信号时生成 bridge。
- 没有 loss signal 时阻断。
- JSON/CSV/JSONL/corpus/TXT/Markdown/HTML writer 和 CLI。

```text
3 passed
```

运行证据：

```text
e/860/解释/bounded-objective-loss-signal-bridge/
e/860/图片/v860-bounded-objective-loss-signal-bridge-html.png
```

Playwright MCP snapshot 确认：

```text
Status=pass
Examples=16
Loss signal=6
Fixed signal=6
Pair reinforce=4
Claim=bridge_corpus_only
```

## 一句话总结

v860 把 profile sweep 的单侧信号整理成无锚点桥接训练语料，为下一次真实训练提供更明确的 `fixed loss` 共现目标。
