# v892 bounded objective loss signal bridge target-only memory stagnation-aware suffix replay delta diagnostic

## 本版目标和边界

v892 的目标是把 v886 和 v891 的 replay 结果做成可复核的 delta 诊断。v891 看到所有 contract surface 都输出了换行开头的 `fixed l`，这看上去比 v886 更整齐，但它是否代表模型能力提升，必须用逐 case delta 判断。

本版明确不做三件事：

- 不重新训练模型。
- 不重新运行 checkpoint replay。
- 不把 `fixed l` 的格式统一解释为 promotion。

它只读取两个既有 replay JSON，检查 pass count、required-term hit count、`loss` 命中和 continuation 表面变化是否一致。

## 前置能力

本版承接三段证据：

- v886：stabilized loss-suffix uptake replay，三条 case 均为 partial required-term hit，其中 canonical 是 `" fixed l"`。
- v891：stagnation-aware suffix replay，三条 case 均为 `"\nfixed l"`。
- v887：已经证明“没有 `loss` 命中时，表面变化不能算 contract gain”。

v892 把这个判断从人工观察变成了独立 diagnostic artifact。

## 关键文件

`src/minigpt/bounded_objective_loss_signal_bridge_target_only_memory_stagnation_aware_suffix_replay_delta_diagnostic.py`

这是核心诊断模块，负责读取两个 replay report 的 summary 和 replay rows，生成 `case_diagnostics`、`diagnostic`、`check_rows`、`summary` 和 `interpretation`。

`src/minigpt/bounded_objective_loss_signal_bridge_target_only_memory_stagnation_aware_suffix_replay_delta_diagnostic_artifacts.py`

这是输出层，负责把同一个 report 写成 JSON、CSV、TXT、Markdown 和 HTML。CSV 保留逐 case delta，HTML 用于截图归档。

`scripts/diagnose_bounded_objective_loss_signal_bridge_target_only_memory_stagnation_aware_suffix_replay_delta.py`

这是命令行入口。它允许输入 replay JSON 文件或输出目录，目录模式会自动定位对应 JSON 文件。`--require-diagnostic-ready` 可以让失败诊断返回非零退出码。

`tests/test_bounded_objective_loss_signal_bridge_target_only_memory_stagnation_aware_suffix_replay_delta_diagnostic.py`

这是测试覆盖，验证通过路径、`loss` 被篡改后的失败路径、case 集缺失后的失败路径，以及 CLI 和五类 artifact 输出。

## 核心数据结构

`case_diagnostics` 是逐 case 诊断表。每行包含：

- `case_id`：契约 case 名，例如 `canonical_direct_completion`。
- `baseline_continuation` / `current_continuation`：v886 和 v891 的输出片段。
- `baseline_hit_terms` / `current_hit_terms`：命中的 required terms。
- `continuation_changed`：输出表面是否变化。
- `loss_newly_hit`：当前 replay 是否新命中 `loss`。
- `space_to_newline_fixed_l`：是否从 `" fixed l"` 变成 `"\nfixed l"`。
- `state_label`：本 case 的诊断状态，例如 `newline_fixed_l_converged_without_loss`。

`diagnostic` 是聚合判断。关键字段包括：

- `pass_delta`
- `any_hit_delta`
- `zero_hit_delta`
- `continuation_changed_count`
- `loss_newly_hit_case_count`
- `current_newline_fixed_l_partial_case_count`
- `space_to_newline_fixed_l_case_count`
- `surface_converged_without_suffix_gain`
- `no_contract_gain_confirmed`

本版最重要的判定是：当所有 current case 都是 `\nfixed l` partial，且 pass/any-hit/zero-hit/loss-new-hit 都没有改善时，报告可以 `pass`，但模型质量结论只能是 `newline_fixed_l_surface_convergence_without_loss_gain`。

## 运行流程

CLI 的流程是：

1. 定位 baseline replay JSON。
2. 定位 current replay JSON。
3. 读取两个 JSON report。
4. 调用 `build_stagnation_aware_suffix_replay_delta_diagnostic()`。
5. 写出 JSON、CSV、TXT、Markdown、HTML。
6. 在 `--require-diagnostic-ready` 下用 `resolve_exit_code()` 决定是否返回失败。

这条链路的输入和输出都是只读证据，不会修改 v886/v891 的历史 artifact。

## 本版实际结果

真实运行结果：

```text
status=pass
decision=bounded_objective_loss_signal_bridge_target_only_memory_stagnation_aware_suffix_replay_newline_fixed_l_converged_without_loss_gain
pass_delta=0
any_hit_delta=0
zero_hit_delta=0
continuation_changed_count=1
space_to_newline_fixed_l_case_count=1
loss_newly_hit_case_count=0
no_contract_gain_confirmed=True
```

这说明 v890/v891 的价值不是“恢复了 fixed loss”，而是“把三个 surface 收敛到了同一种 fixed-l partial 格式”。它减少了表面不稳定，但没有解决 `loss` 后缀。

## 测试覆盖

测试保护了四个关键点：

- 正常 v886/v891 delta 必须通过，并给出 surface convergence without suffix gain。
- 如果 current replay 新命中 `loss`，本诊断不能继续当作 no-gain 结论，必须失败。
- 如果 current replay 缺少 case，必须失败，避免拿不同 case set 做比较。
- CLI 必须能从目录定位 JSON，并写出 JSON、CSV、TXT、Markdown、HTML 五类输出。

## 运行证据

运行证据保存在：

- `e/892/解释/说明.md`
- `e/892/解释/bounded-objective-loss-signal-bridge-target-only-memory-stagnation-aware-suffix-replay-delta-diagnostic/`
- `e/892/图片/v892-bounded-objective-loss-signal-bridge-target-only-memory-stagnation-aware-suffix-replay-delta-diagnostic-html.png`

截图证明 HTML artifact 可以被浏览器打开，且核心字段 `status=pass`、`pass_delta=0`、`loss_newly_hit_case_count=0` 和下一步概率探针路线可见。

## 一句话总结

v892 把 v891 的“换行 fixed-l 统一”降级为 surface convergence evidence，而不是能力提升证据，并把下一步从继续堆数据转向 loss-token probability probe。
