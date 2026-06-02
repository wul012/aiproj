# v769 objective-level contrast seed 3737 pair-probe replay 代码讲解

## 本版目标和边界

v769 的目标是消费 v768 的 seed `3737` checkpoint，运行 fixed-preserving transfer pair-probe replay。v768 已经证明训练内 direct probes 能 pair-full；v769 要验证这个信号能否在独立 replay artifact 中复现。

本版不训练、不改变 corpus、不改变模型规模，也不把 seed `3737` 单独接受为最终能力结论。

## 前置路线

- v767 seed stability plan 指定补充 seed `3737` 和 `3838`。
- v768 完成 seed `3737` 训练，得到 direct pair-full。
- v769 对 v768 checkpoint 运行 heldout pair-probe replay。

## 本版复用的关键文件

- `scripts/run_model_capability_required_term_pair_readiness_fixed_preserving_transfer_pair_probe_replay.py`
  - pair-probe replay CLI。
  - 输入 training run 目录，定位 checkpoint/tokenizer/config，并输出 replay report。

- `src/minigpt/model_capability_required_term_pair_readiness_fixed_preserving_transfer_pair_probe_replay.py`
  - replay 核心逻辑。
  - 运行 exact、spaced、arrow 等 pair probe surface，判断是否满足 required pair-full。

- `src/minigpt/model_capability_required_term_pair_readiness_fixed_preserving_transfer_pair_probe_replay_artifacts.py`
  - 输出 JSON、CSV、TXT、Markdown 和 HTML。

v769 没有新增代码文件，原因是 replay runner 已经在 v764 证明可复用。本版的增量是新的 seed replay 证据。

## 输入输出结构

输入：

```text
e/768/解释/model-capability-required-term-pair-readiness-objective-level-contrast-seed-3737-training-run
```

输出：

```text
e/769/解释/model-capability-required-term-pair-readiness-objective-level-contrast-seed-3737-pair-probe-replay
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

`required_all_pair_full=True` 是本版通过的关键；`pair_full_count=2` 是强度信号，后续 rollup 需要与 v764 的 `pair_full_count=3` 一起比较。

## 测试和验证

本版复用已有 replay runner，不新增测试文件。验证重点是：

- CLI 返回 `status=pass`。
- HTML 页面可见 exact pair 和 required all 都为 true。
- pair-full count 被记录，而不是只保留 pass/fail。

Playwright 截图位于：

```text
e/769/图片/v769-objective-level-contrast-seed-3737-pair-probe-replay.png
```

## 链路角色

v769 是 objective-level contrast seed stability 的第二个 replay-ready seed。它增加了稳定性信心，但也暴露了强度差异：seed `3737` 可过 required gate，但 pair-full 计数低于 seed `3636`。

一句话总结：v769 证明 objective-level contrast 已经有第二个 seed 的 replay 支撑，但还需要 seed `3838` 和 rollup 才能进入接受审查。
