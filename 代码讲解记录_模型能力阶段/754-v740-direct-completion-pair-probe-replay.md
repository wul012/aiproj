# v740 direct-completion pair-probe replay

## 本版目标和边界

v740 的目标是复核 v739 选中的 direct-completion route candidate。

v738 已经在 heldout direct probes 上 pair-full，v739 也确认它相对 v729/v733 有明确提升。但 promotion 前还要回答一个更难的问题：同一个 checkpoint 面对 heldout pair prompt，例如 `fixed=|loss=`，是否还能同时输出 fixed 和 loss。

本版不训练、不改 corpus、不做 promotion。它只做 replay 检查。

## 前置链路

```text
v738 direct-completion surface training
 -> fixed= / loss= direct probes pair-full
v739 direct-completion route comparison
 -> selected_route = direct-completion-surface
v740 pair-probe replay
 -> test fixed=|loss= transfer without retraining
```

## 关键新增文件

- `src/minigpt/model_capability_required_term_pair_readiness_direct_completion_pair_probe_replay.py`
  - 读取 v739 route comparison。
  - 定位 selected direct-completion training report。
  - 将 pair prompt spec 转成 generation-profile replay source。
  - 汇总 exact heldout pair 是否 pair-full。
- `src/minigpt/model_capability_required_term_pair_readiness_direct_completion_pair_probe_replay_artifacts.py`
  - 输出 JSON/CSV/TXT/Markdown/HTML。
  - 将每个 prompt spec 的 generation-profile replay 作为 sidecar 写出。
- `scripts/run_model_capability_required_term_pair_readiness_direct_completion_pair_probe_replay.py`
  - CLI 入口，支持自定义 prompt spec、profiles、device。
- `tests/test_model_capability_required_term_pair_readiness_direct_completion_pair_probe_replay.py`
  - 使用 mock generator 覆盖 ready、not-ready、错误 comparison 和五格式输出。
- `src/minigpt/model_capability_required_term_pair_generation_profile_replay_artifacts.py`
  - 对 CSV 中的 `continuation_preview` 做 `rstrip()`。
  - 这是为了防止真实生成文本末尾空格进入 sidecar CSV 后触发 `git diff --check`。

## replay 设计

v740 默认 prompt specs：

```text
exact-heldout-pair: fixed=|loss=   required_for_ready=True
spaced-heldout-pair: fixed= | loss=
arrow-heldout-pair: fixed -> | loss ->
```

每个 spec 都会被转成一个 generation-profile replay source：

```text
term=fixed, scaffold_prompt=<pair prompt>
term=loss, scaffold_prompt=<pair prompt>
```

同一 prompt 下两个 term 都命中，才算 pair-full。

## 真实结果

命令行摘要：

```text
decision=pair_readiness_direct_completion_pair_probe_replay_not_ready
pair_full_count=0
required_all_pair_full=False
exact_heldout_pair_full=False
```

sidecar replay 观察：

- exact `fixed=|loss=` 生成类似 `los los toss`，fixed/loss 都未命中。
- spaced `fixed= | loss=` 只部分命中 loss。
- arrow `fixed -> | loss ->` 也没有 pair-full。

这说明 v738 的能力边界是 direct probe，不是 pair prompt transfer。

## 决策逻辑

只有 required prompt specs 全部 pair-full，才输出：

```text
pair_readiness_direct_completion_pair_probe_replay_ready
```

真实 v740 输出：

```text
pair_readiness_direct_completion_pair_probe_replay_not_ready
```

因此模型质量声明保持：

```text
model_quality_claim=not_claimed
```

## 测试覆盖

测试覆盖：

- exact pair prompt 同时命中 fixed/loss 时 ready。
- exact pair prompt 只命中 fixed 时 not-ready。
- v739 comparison decision 不正确时 fail。
- JSON/CSV/TXT/Markdown/HTML 和 sidecar replay 输出完整。
- generation-profile replay CSV 会收束 `continuation_preview` 末尾空格，保护 CI whitespace gate。

## 证据

运行输出：

```text
e/740/解释/model-capability-required-term-pair-readiness-direct-completion-pair-probe-replay/
```

截图：

```text
e/740/图片/v740-direct-completion-pair-probe-replay.png
```

截图可见：

- `Decision=pair_readiness_direct_completion_pair_probe_replay_not_ready`
- `Pair-full=0/3`
- `Required all=False`
- `Exact pair=False`

## 一句话总结

v740 阻止了对 v738 的过度 promotion，把当前能力边界准确收缩为 direct-probe-only，并把下一步指向 pair prompt transfer repair。
