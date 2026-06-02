# v771 objective-level contrast seed 3838 pair-probe replay 代码讲解

## 本版目标和边界

v771 消费 v770 的 seed `3838` checkpoint，运行 heldout pair-probe replay。它是 v767 seed stability plan 的最后一个 replay 输入。

本版不训练，不改 corpus，不调解码参数，也不直接接受 objective-level contrast。它只产出第三个 seed 的 replay-ready 证据。

## 前置路线

- v764：seed `3636` replay-ready，`pair_full_count=3`。
- v769：seed `3737` replay-ready，`pair_full_count=2`。
- v771：seed `3838` replay-ready，`pair_full_count=2`。

这三份 replay 是 v772 seed stability rollup 的输入。

## 本版复用的关键文件

- `scripts/run_model_capability_required_term_pair_readiness_fixed_preserving_transfer_pair_probe_replay.py`
  - replay CLI。
  - 接收 training run 目录并定位 checkpoint/tokenizer。

- `src/minigpt/model_capability_required_term_pair_readiness_fixed_preserving_transfer_pair_probe_replay.py`
  - replay 核心逻辑。
  - 判断 exact heldout pair 和 required all pair-full 是否成立。

- `src/minigpt/model_capability_required_term_pair_readiness_fixed_preserving_transfer_pair_probe_replay_artifacts.py`
  - 生成 JSON、CSV、TXT、Markdown 和 HTML。

本版没有新增代码，因为 replay runner 已经是稳定工具；新增价值是 seed `3838` 的真实 replay artifact。

## 输入输出结构

输入：

```text
e/770/解释/model-capability-required-term-pair-readiness-objective-level-contrast-seed-3838-training-run
```

输出：

```text
e/771/解释/model-capability-required-term-pair-readiness-objective-level-contrast-seed-3838-pair-probe-replay
```

核心字段：

```text
status=pass
decision=pair_readiness_fixed_preserving_transfer_pair_probe_replay_ready
exact_heldout_pair_full=True
required_all_pair_full=True
pair_full_count=2
model_quality_claim=pair_probe_replay_ready
```

## 运行证据和边界

Playwright 截图位于：

```text
e/771/图片/v771-objective-level-contrast-seed-3838-pair-probe-replay.png
```

截图显示 replay 页面中 exact pair、required all 均为 true，pair-full count 为 2。这个结果与 seed `3737` 一致，低于 seed `3636` 的 count 3，所以 rollup 应同时记录“稳定通过”和“强度不完全一致”。

一句话总结：v771 让 objective-level contrast 的 seed stability 输入齐备，下一版可以做三 seed rollup。
