# v879：bounded objective loss signal bridge target-only memory loss-suffix replay regression diagnostic

## 本版目标和边界

v879 的目标是解释 v877 到 v878 之间看起来“矛盾”的现象：v877 的训练 sample 已经输出完整 `fixed loss`，但 v878 的固定 contract replay 仍然 `passed_case_count=0`，并且 completion surface 从 v874 的 partial hit 退回 zero-hit。

本版不训练新模型，不修改 v836 bounded objective contract，也不直接生成下一轮训练语料。它只做诊断，把 sample、baseline replay 和 current replay 三类证据放到同一份报告里，避免后续把单条 sample success 误判为 contract recovery。

## 前置链路

```text
v874 target-only memory replay comparison
 -> v875 partial-hit diagnostic
 -> v876 loss-suffix patch
 -> v877 loss-suffix training run
 -> v878 loss-suffix replay comparison
 -> v879 loss-suffix replay regression diagnostic
```

v879 的角色是“路线纠偏”：v876/v877 的 loss-suffix 数据确实让 sample 变好，但 v878 说明这种改善没有稳定迁移到三条 objective surfaces。诊断结果会把下一步路由到 completion surface stabilization patch。

## 关键新增文件

- `src/minigpt/bounded_objective_loss_signal_bridge_target_only_memory_loss_suffix_replay_regression_diagnostic.py`
  - 核心诊断模块。
  - 读取 current replay、baseline replay 和 sample text。
  - 计算 `any_hit_delta`、`zero_hit_delta`、`sample_contract_gap`、`completion_surface_regressed_to_zero`。
  - 输出 `model_quality_claim=sample_success_contract_regression`。

- `src/minigpt/bounded_objective_loss_signal_bridge_target_only_memory_loss_suffix_replay_regression_diagnostic_artifacts.py`
  - 输出 JSON、CSV、TXT、Markdown、HTML。
  - HTML 报告将关键 deltas、当前 replay cases、baseline replay cases 放在同一页。

- `scripts/diagnose_bounded_objective_loss_signal_bridge_target_only_memory_loss_suffix_replay_regression.py`
  - CLI 入口。
  - 支持目录或 JSON 文件输入。
  - `--require-diagnostic-ready` 下如果诊断不成立会返回非零退出码。

- `tests/test_bounded_objective_loss_signal_bridge_target_only_memory_loss_suffix_replay_regression_diagnostic.py`
  - 覆盖 sample success + replay regression 的通过场景。
  - 覆盖 sample 不含 `fixed loss` 时失败。
  - 覆盖 replay signal 没有回归时失败。
  - 覆盖 writer 和 CLI。

## 核心数据结构

### sample_diagnostic

`sample_diagnostic` 从 v877 `sample.txt` 提取最小事实：

```text
sample_fixed_loss=True
sample_fixed=True
sample_loss=True
sample_tail=...
```

它只证明训练样本输出里出现过 `fixed loss`，不承担 contract 能力证明。

### regression

`regression` 是 v879 的关键判断层：

```text
sample_contract_gap=True
objective_contract_recovered=False
current_any_hit_case_count=2
baseline_any_hit_case_count=3
any_hit_delta=-1
current_zero_hit_case_count=1
baseline_zero_hit_case_count=0
zero_hit_delta=1
completion_surface_regressed_to_zero=True
fixed_l_partial_case_count=2
```

这些字段把“sample 成功”和“replay 退化”拆开看。`sample_contract_gap=True` 表示 sample 出现完整目标，但固定 objective contract 仍未恢复。`completion_surface_regressed_to_zero=True` 表示 completion label 这条 surface 从 v874 的 partial hit 退回 zero-hit，是下一版最应该修的点。

### case_diagnostics

每条 replay row 会被归类：

```text
fixed_l_partial
completion_surface_zero_regression
fixed_without_loss
zero_hit
```

v879 的真实结果中，canonical/minimal 两条都是 `fixed_l_partial`，completion label 是 `completion_surface_zero_regression`。

## 真实运行流程

本版真实命令：

```text
python scripts/diagnose_bounded_objective_loss_signal_bridge_target_only_memory_loss_suffix_replay_regression.py --current-replay-comparison e/878/解释/bounded-objective-loss-signal-bridge-target-only-memory-loss-suffix-replay-comparison --baseline-replay-comparison e/874/解释/bounded-objective-loss-signal-bridge-target-only-memory-replay-comparison --sample e/877/解释/bounded-objective-loss-signal-bridge-target-only-memory-loss-suffix-training-run/run/sample.txt --out-dir e/879/解释/bounded-objective-loss-signal-bridge-target-only-memory-loss-suffix-replay-regression-diagnostic --require-diagnostic-ready --force
```

真实输出：

```text
status=pass
decision=bounded_objective_loss_signal_bridge_target_only_memory_loss_suffix_sample_success_contract_regression
loss_suffix_replay_regression_diagnostic_ready=True
sample_contract_gap=True
objective_contract_recovered=False
any_hit_delta=-1
zero_hit_delta=1
completion_surface_regressed_to_zero=True
fixed_l_partial_case_count=2
model_quality_claim=sample_success_contract_regression
next_action=build_bounded_objective_loss_signal_bridge_target_only_memory_completion_surface_stabilization_patch
```

## 测试覆盖

focused 测试：

```text
python -m pytest tests/test_bounded_objective_loss_signal_bridge_target_only_memory_loss_suffix_replay_regression_diagnostic.py -q -o cache_dir=runs/pytest-cache-v879-focused
```

结果：

```text
4 passed
```

测试保护了三个边界：

- sample 必须真的包含 `fixed loss`，否则不能做 sample-contract-gap 结论。
- current replay 必须相对 baseline 出现 `any_hit_delta < 0` 或 `zero_hit_delta > 0`，否则不能叫 regression。
- completion surface 必须能解释 zero-hit regression，否则下一步不能直接路由到 surface stabilization。

## 运行证据

- 解释目录：`e/879/解释/bounded-objective-loss-signal-bridge-target-only-memory-loss-suffix-replay-regression-diagnostic/`
- 截图目录：`e/879/图片/`
- Playwright MCP 截图：`e/879/图片/v879-bounded-objective-loss-signal-bridge-target-only-memory-loss-suffix-replay-regression-diagnostic-html.png`

## 一句话总结

v879 把 loss-suffix route 的“sample 成功但 contract 未恢复”固化为可测试诊断，并把下一步从继续补 suffix 转向 completion surface stabilization。
