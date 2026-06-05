# v882：bounded objective loss signal bridge target-only memory completion-surface stabilization replay comparison

## 本版目标和边界

v882 的目标是验证 v881 checkpoint 的真实 contract 表现。v881 sample 已经在 completion prompt 下输出 `fixed loss`，但项目规则一直明确：sample 不能替代 fixed objective replay。

本版不训练，不改 v836 contract，不做 holdout promotion。它只用 v836 三条 bounded objective cases 回放 v881 checkpoint，并记录真实结果。

## 前置链路

```text
v879 replay regression diagnostic
 -> v880 completion-surface stabilization patch
 -> v881 completion-surface stabilization training run
 -> v882 completion-surface stabilization replay comparison
```

v882 是 v880/v881 的验收版：它回答 completion surface regression 是否被修回，以及 full `fixed loss` contract 是否恢复。

## 关键新增文件

- `src/minigpt/bounded_objective_loss_signal_bridge_target_only_memory_completion_surface_stabilization_replay_comparison.py`
  - v882 replay adapter。
  - 复用通用 `build_bounded_objective_loss_signal_bridge_replay_comparison()`。
  - 将 v881 training ready 字段映射到通用 replay engine。
  - route 标记为 `bounded_objective_loss_signal_bridge_target_only_memory_completion_surface_stabilization`。

- `src/minigpt/bounded_objective_loss_signal_bridge_target_only_memory_completion_surface_stabilization_replay_comparison_artifacts.py`
  - 复用 bounded objective replay renderer。
  - 替换标题和 ready 字段。

- `scripts/run_bounded_objective_loss_signal_bridge_target_only_memory_completion_surface_stabilization_replay_comparison.py`
  - CLI 入口。
  - 支持 objective contract、training run、checkpoint、tokenizer、device 和 require flags。

- `tests/test_bounded_objective_loss_signal_bridge_target_only_memory_completion_surface_stabilization_replay_comparison.py`
  - 覆盖 partial-hit、contract recovered still holdout required、training not ready fail、writer 和 CLI。

## 真实回放结果

```text
objective_contract_recovered=False
passed_case_count=0
any_hit_case_count=3
zero_hit_case_count=0
promotion_ready=False
```

三条 replay row：

```text
canonical_direct_completion -> " fixed l"
minimal_direct_completion   -> " fixed l"
completion_label_surface    -> " fixed l"
```

这说明 completion surface stabilization 做到了一半：它把 v878 的 `completion_label_surface` 从 `an: fix` 拉回 `fixed l`，但还没有把 `fixed l` 补全成 `fixed loss`。

## 与 v878 的差异

```text
v878: any_hit_case_count=2, zero_hit_case_count=1, completion_label_surface="\nan: fix"
v882: any_hit_case_count=3, zero_hit_case_count=0, completion_label_surface=" fixed l"
```

所以 v882 的合理结论是 `partial_required_term_signal`，不是 `contract_recovered`。下一步不是继续修 completion label，而是诊断 stabilized state 下为什么 `loss` suffix 仍未完整输出。

## 测试覆盖

focused 测试：

```text
python -m pytest tests/test_bounded_objective_loss_signal_bridge_target_only_memory_completion_surface_stabilization_replay_comparison.py -q -o cache_dir=runs/pytest-cache-v882-focused
```

结果：

```text
4 passed
```

测试保护：

- partial-hit replay 只能 ready，不能 recovered。
- contract recovered 仍然必须 holdout required。
- training not ready 时 replay 必须 fail。
- writer 和 CLI 必须输出 JSON、CSV、TXT、Markdown、HTML。

## 运行证据

- 解释目录：`e/882/解释/bounded-objective-loss-signal-bridge-target-only-memory-completion-surface-stabilization-replay-comparison/`
- 截图目录：`e/882/图片/`
- Playwright MCP 截图：`e/882/图片/v882-bounded-objective-loss-signal-bridge-target-only-memory-completion-surface-stabilization-replay-comparison-html.png`

## 一句话总结

v882 证明 completion surface regression 已被拉回 partial signal，但 full objective contract 仍卡在 `fixed l` 到 `loss` 的 suffix uptake gap。
