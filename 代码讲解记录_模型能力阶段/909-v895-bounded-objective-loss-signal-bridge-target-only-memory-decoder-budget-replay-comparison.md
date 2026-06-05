# v895 bounded objective loss signal bridge target-only memory decoder-budget replay comparison

## 本版目标和边界

v895 的目标是把 v894 的预算审计变成真实 replay 复核。v894 已经证明 v891 的 `max_new_tokens=8` 刚好卡在 `\nfixed l`，而 v893 证明 `oss` 是 top-1。v895 因此只把 replay budget 改成 11，保持 checkpoint、tokenizer、contract、temperature、top-k、seed 不变。

本版不重新训练，不修改 contract，也不直接 promotion。它只回答一个问题：同一个 v890 checkpoint 在 11-token replay budget 下，能否通过 v836 objective contract？

## 前置能力

本版承接：

- v890：真实 stagnation-aware suffix checkpoint。
- v891：8-token replay 停在 `\nfixed l`。
- v893：`fixed l` 后 `oss` 全部 top-1。
- v894：确认 8-token budget 耗尽，推荐 `max_new_tokens=11`。

v895 是这条证据链的实际复核版。

## 关键文件

`src/minigpt/bounded_objective_loss_signal_bridge_target_only_memory_decoder_budget_replay_comparison.py`

核心 replay wrapper。它读取 objective contract、v890 training run 和 v894 decoder budget audit，取 `recommended_max_new_tokens=11`，然后复用已有 `build_stagnation_aware_suffix_replay_comparison()`。

`src/minigpt/bounded_objective_loss_signal_bridge_target_only_memory_decoder_budget_replay_comparison_artifacts.py`

artifact 输出层。它复用已有 replay comparison renderer，改写 title 和 ready 字段，输出 JSON、CSV、TXT、Markdown、HTML。

`scripts/run_bounded_objective_loss_signal_bridge_target_only_memory_decoder_budget_replay_comparison.py`

CLI 入口。支持 `--require-comparison-ready` 和 `--require-objective-pass`，本版真实运行两者都通过。

`tests/test_bounded_objective_loss_signal_bridge_target_only_memory_decoder_budget_replay_comparison.py`

测试覆盖 contract recovered、budget audit 不 ready、partial replay、CLI 输出四类情况。

## 核心流程

`build_decoder_budget_replay_comparison()` 的流程是：

1. 读取 v894 decoder budget audit summary。
2. 取 `recommended_max_new_tokens`，真实值为 11。
3. 构造 `_budget_runner(max_new_tokens)`。
4. 调用既有 stagnation-aware suffix replay comparison。
5. 追加 decoder budget audit checks。
6. 把 decision、summary、interpretation 改写成 decoder-budget route。

这个设计避免复制 replay scoring 逻辑，也保留已有 contract case scoring、hit/miss 判定和 CSV 输出。

## 关键检查

本版新增的 budget checks 包括：

- `decoder_budget_audit_passed`
- `decoder_budget_audit_ready`
- `recommended_budget_present`

这些检查保证 v895 不是随意提高 generation length，而是严格来自 v894 的审计结论。

## 本版真实结果

真实运行结果：

```text
status=pass
decision=bounded_objective_loss_signal_bridge_target_only_memory_decoder_budget_replay_contract_recovered_holdout_required
objective_contract_recovered=True
canonical_case_pass=True
passed_case_count=3
any_hit_case_count=3
zero_hit_case_count=0
pass_rate=1.0
```

逐 case continuation：

```text
canonical_direct_completion -> "\nfixed loss"
minimal_direct_completion -> "\nfixed loss"
completion_label_surface -> "\nfixed loss"
```

这说明 v890 checkpoint 本身已经具备输出完整 `fixed loss` 的能力，v891 的失败来自 replay budget 过短。

## 为什么仍不 promotion

v895 的 `model_quality_claim` 是 `objective_contract_recovered_only`。这不是最终 promotion，因为 v836 contract 是当前修复路线的目标集，还需要 unchanged holdout replay 验证泛化。

因此下一步是 `run_unchanged_bounded_suite_holdout_replay`，而不是“宣布模型已经完全提升”。

## 测试覆盖

测试覆盖：

- 三条 fake replay 都输出 `fixed loss` 时，contract recovered 且下一步是 holdout。
- budget audit 不 ready 时，report 必须 fail。
- 只有一条 case 通过时，report 保持 partial，不允许 objective pass。
- CLI 可以用 tiny checkpoint/tokenizer 跑通真实加载和输出。

## 运行证据

运行证据保存在：

- `e/895/解释/说明.md`
- `e/895/解释/bounded-objective-loss-signal-bridge-target-only-memory-decoder-budget-replay-comparison/`
- `e/895/图片/v895-bounded-objective-loss-signal-bridge-target-only-memory-decoder-budget-replay-comparison-html.png`

截图证明 HTML artifact 可打开，并展示 `objective_contract_recovered=True`、`passed_case_count=3` 和 holdout next action。

## 一句话总结

v895 用 11-token replay 证明同一个 v890 checkpoint 可以恢复 bounded objective contract，但仍把 promotion 挡在 unchanged holdout replay 之前。
