# v528 model capability required-term pair loss-alias fresh seed sweep 代码讲解

## 本版目标与边界

v528 的目标是把 v527 的 fresh compare 从单 seed 扩展到多 seed sweep。v527 发现 seed `527` 默认解码已经 strict `4/4`，这说明不能简单把 strict recovery 归功于 blocked-token 解码。但单 seed 也不能证明 fresh training 已经稳定。

本版因此新增 sweep 报告：同一组训练配置下跑 seeds `527,528,529`，每个 seed 都保留默认解码和 blocked-token 解码的对照，并在 seed 层面判断稳定性。

本版不扩大模型，不改训练目标，也不把 blocked-token 设为默认。它只回答“多 seed 下 baseline 和 explicit profile 哪个更稳定”。

## 前置链路

前置版本：

- v526：`GenerationRequest.blocked_token_texts` 接入 core generator。
- v527：fresh compare 证明 seed `527` 默认解码已经 strict full，blocked-token 没有新增 gain。

v528 接着验证 seed `527` 是否代表稳定现象。

## 关键文件

- `src/minigpt/model_capability_required_term_pair_loss_alias_fresh_seed_sweep.py`
  - 新增多 seed sweep builder。
  - 复用 v527 `build_model_capability_required_term_pair_loss_alias_blocked_token_fresh_compare()`，避免复制训练和 probe 逻辑。
  - 从 nested compare report 中抽取 `seed_rows`。
- `src/minigpt/model_capability_required_term_pair_loss_alias_fresh_seed_sweep_artifacts.py`
  - 输出 JSON、CSV、text、Markdown、HTML。
  - 同时写出 `fresh-compare-report/` sidecar，保留 v527 子报告。
- `scripts/run_model_capability_required_term_pair_loss_alias_fresh_seed_sweep.py`
  - 提供 CLI，默认 seeds 为 `527 528 529`。
  - 支持训练超参和 `--require-pass`。
- `tests/test_model_capability_required_term_pair_loss_alias_fresh_seed_sweep.py`
  - 覆盖 baseline stable、blocked-token stable recovery 和 sidecar 输出。
- `e/528/解释/说明.md`
  - 记录真实多 seed 运行结果和结论边界。

## 核心数据结构

v528 主报告新增 `seed_rows`：

```text
seed
status
checkpoint_exists
case_count
baseline_strict_hit_count
baseline_strict_full_coverage
blocked_token_strict_hit_count
blocked_token_strict_full_coverage
blocked_token_strict_gain_count
fresh_focus_strict_full_coverage
fresh_focus_newline_cleanup_full_coverage
```

这些字段让报告可以直接回答：

- 哪些 seed 默认解码已经 strict full。
- 哪些 seed 需要 blocked-token 才 strict full。
- blocked-token 的新增 gain 是否集中在某个 seed。

`summary` 再把 seed rows 汇总为：

```text
baseline_strict_full_seed_count
blocked_token_strict_full_seed_count
blocked_token_gain_seed_count
total_blocked_token_strict_gain_count
stable_baseline_strict_full_coverage
stable_blocked_token_strict_full_coverage
```

## 核心流程

1. CLI 读取 v515 loss-alias stability report。
2. sweep builder 以 seeds `527,528,529` 调用 v527 fresh compare builder。
3. v527 builder 负责真实训练、默认解码和 blocked-token probe。
4. sweep builder 从 nested `fresh_focus_report.seed_reports` 和 `blocked_token_probe_report.case_rows` 按 seed 聚合。
5. artifact writer 输出主 sweep 报告，并保留 compare sidecar。

这种做法的好处是：v528 只新增 seed 级稳定性判断，不重复实现训练和解码 probe，职责边界清楚。

## 真实结果解释

v528 真实运行结果：

```text
seed_count=3
baseline_strict_full_seed_count=2
blocked_token_strict_full_seed_count=3
blocked_token_gain_seed_count=1
total_blocked_token_strict_gain_count=2
```

逐 seed：

```text
527: baseline 4/4, blocked-token 4/4, gains 0
528: baseline 2/4, blocked-token 4/4, gains 2
529: baseline 4/4, blocked-token 4/4, gains 0
```

结论要分两层：

- fresh training 的确比旧 checkpoint 更强，因为 2/3 seeds 默认就 strict full。
- blocked-token profile 仍有价值，因为它把 3/3 seeds 都拉到 strict full，并对 seed `528` 提供新增 gain。

因此下一步更合理的是把 blocked-token 作为显式 profile 接到 playground/API 可选项，而不是默认开启。

## 测试覆盖

新增测试覆盖：

- 两个 fake seeds 默认都输出 `loss` 时，报告应判定 `baseline_stably_strict`。
- 默认输出 `lo\ns\ns`、blocked-token 输出 `loss` 时，报告应判定 `blocked_token_stably_recovers`。
- artifacts writer 必须写出主报告和 `fresh-compare-report/` sidecar。

测试保护的是 seed 级聚合语义：单 seed gain 不能被误判为 baseline 稳定，baseline 稳定时也不能把 blocked-token 说成新增恢复。

## 运行证据

运行证据归档在：

```text
e/528/解释/model-capability-required-term-pair-loss-alias-fresh-seed-sweep/
e/528/图片/
```

截图：

```text
e/528/图片/01-model-capability-required-term-pair-loss-alias-fresh-seed-sweep.png
```

截图中 `Baseline full=2`、`Blocked full=3`、`Blocked gains=2` 是本版核心证据。

## 一句话总结

v528 把 loss-alias fresh recovery 从单 seed 观察推进到 3 seed 稳定性对照，确认 fresh baseline 已显著变强，但 blocked-token profile 仍是更稳定的显式解码兜底。
