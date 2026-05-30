# v527 model capability required-term pair loss-alias blocked-token fresh compare 代码讲解

## 本版目标与边界

v527 的目标是把 v526 已落入 core generator 的 `blocked_token_texts` 能力放到 fresh training checkpoint 上复验。前几版已经证明旧 focus checkpoint 在屏蔽 newline token 后可以从 strict `0/4` 恢复到 `4/4`；但这还不能说明后续训练一定依赖 blocked-token 解码。

本版因此新增一个聚合型报告：先重新训练一个 loss-alias focus checkpoint，再对同一个 checkpoint 分别执行默认解码和 blocked-token 解码，最后在一份报告里说明 strict hit 来自哪里。

本版不做两件事：

- 不把 blocked-token profile 设置为默认生成策略。
- 不把单个 fresh seed 的结果包装成稳定模型能力结论。

## 前置链路

前置版本：

- v523：主 focus 报告中加入 newline cleanup 指标，确认 `loss` 是被换行切开。
- v524：单 checkpoint 证明屏蔽 newline token 可把 strict hit 从 `0/4` 恢复到 `4/4`。
- v525：跨两个历史 focus checkpoints 复验 newline suppression 恢复信号。
- v526：把 blocked-token 解码接入 `GenerationRequest`、`MiniGPTGenerator` 和 core model sampling。

v527 接在 v526 后面，验证这条正式 generator path 在 fresh training 上如何表现。

## 关键文件

- `src/minigpt/model_capability_required_term_pair_loss_alias_blocked_token_fresh_compare.py`
  - 新增 fresh compare builder。
  - 调用既有 focus builder 生成 fresh checkpoint。
  - 再调用 newline suppression probe，对同一 checkpoint 做默认解码和 blocked-token 解码对照。
  - 汇总 `baseline_strict_hit_count`、`blocked_token_strict_hit_count` 和 `blocked_token_strict_gain_count`。
- `src/minigpt/model_capability_required_term_pair_loss_alias_blocked_token_fresh_compare_artifacts.py`
  - 负责 JSON、CSV、text、Markdown、HTML 输出。
  - 同时写出 `fresh-focus-report/` 和 `blocked-token-probe-report/` 两个 sidecar，保留可追溯子报告。
- `scripts/run_model_capability_required_term_pair_loss_alias_blocked_token_fresh_compare.py`
  - 提供 CLI 入口。
  - 支持训练参数、seed、输出目录、`--force` 和 `--require-pass`。
- `tests/test_model_capability_required_term_pair_loss_alias_blocked_token_fresh_compare.py`
  - 用 fake train/generate 覆盖恢复路径、sidecar 输出和失败输入。
- `e/527/解释/说明.md`
  - 记录真实命令、结果解释、截图和产物边界。

## 核心数据结构

主报告包含三层证据：

```text
fresh_focus_report
blocked_token_probe_report
summary
```

`fresh_focus_report` 是重新训练得到的 focus 报告，包含 checkpoint、tokenizer、corpus、generation rows 和 focus summary。

`blocked_token_probe_report` 复用 v526 的 generator path，对同一 checkpoint 跑两个 profile：

- `baseline_rerun`
- `suppress_newline_tokens`

`summary` 把两个子报告压缩成可决策字段：

```text
baseline_strict_hit_count
baseline_strict_full_coverage
blocked_token_strict_hit_count
blocked_token_strict_full_coverage
blocked_token_strict_gain_count
fresh_focus_decision
fresh_focus_surface_decision
blocked_token_surface_decision
```

这里最关键的是 `blocked_token_strict_gain_count`。如果 baseline 已经是 strict `4/4`，则 blocked-token 不能被说成带来恢复增益。

## 核心流程

1. CLI 读取 v515 loss-alias stability report。
2. fresh compare builder 创建 `fresh-focus-run/`。
3. focus builder 重新生成 focus corpus 并训练 tiny checkpoint。
4. fresh checkpoint 先走默认解码，生成 baseline rows。
5. 同一 checkpoint 再传入 `blocked_token_texts=("\n", "\r")` 生成 suppressed rows。
6. compare summary 对比 baseline strict 与 blocked-token strict。
7. artifacts writer 写出主报告和两个 sidecar 子报告。

这个结构避免了两个风险：一是只看旧 checkpoint 导致结论滞后，二是只看 blocked-token 输出而忽略 baseline 已经变强。

## 真实结果解释

v527 真实运行结果：

```text
baseline_strict_hit_count=4
blocked_token_strict_hit_count=4
blocked_token_strict_gain_count=0
decision=required_term_pair_loss_alias_blocked_token_fresh_baseline_already_strict
```

这说明 seed `527` 的 fresh focus checkpoint 默认解码已经严格输出 `loss`。因此本版结论不是“blocked-token 又恢复了 strict hit”，而是“fresh training seed 已经足够强，blocked-token 没有新增增益”。

这个结果比单纯继续堆 suppression 证据更有价值，因为它把模型能力提升和解码补救拆开了。

## 测试覆盖

新增测试覆盖三类边界：

- fake focus baseline 输出 `lo\ns\ns`，blocked-token probe 输出 `loss`，报告应判定 strict recovery。
- artifacts writer 必须同时生成主报告和 `fresh-focus-report/`、`blocked-token-probe-report/` sidecar。
- 当 source stability 没有 missed focus rows 时，fresh focus 无法成立，compare 必须结构失败并在 `--require-pass` 下返回非零。

这些断言保护的是链路语义，而不是单纯的文件存在：fresh compare 必须能区分训练本身变强与 blocked-token 解码带来的增益。

## 运行证据

运行证据归档在：

```text
e/527/解释/model-capability-required-term-pair-loss-alias-blocked-token-fresh-compare/
e/527/图片/
```

截图：

```text
e/527/图片/01-model-capability-required-term-pair-loss-alias-blocked-token-fresh-compare.png
```

截图中 `Baseline strict=4`、`Blocked strict=4`、`Strict gains=0` 是本版的核心证据。

## 一句话总结

v527 把 blocked-token decoding 从旧 checkpoint 复验推进到 fresh checkpoint 对照，并证明 seed `527` 的 strict recovery 主要来自新训练本身，而不是解码屏蔽增益。
