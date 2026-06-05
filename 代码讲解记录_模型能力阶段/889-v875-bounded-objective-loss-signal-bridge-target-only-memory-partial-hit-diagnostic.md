# v875：bounded objective loss signal bridge target-only memory partial-hit diagnostic

## 本版目标和边界

v875 的目标是解释 v874 的 partial-hit replay。v874 已经证明 target-only memory training 有效：三条 case 都从 zero-hit 变成命中 `fixed`。但它还没有恢复完整 `fixed loss`。v875 把这个结果转成一个更窄的诊断：`loss_suffix_uptake_gap`。

本版不训练，不 replay，不修改 v836 contract，不声称模型已经通过目标。它只为下一版 patch 选择方向。

## 前置链路

```text
v873 target-only memory training
 -> v874 target-only memory replay partial-hit
 -> v875 loss suffix diagnostic
```

这版的重要性在于避免盲目继续训练。既然三条 case 都已经到达 `fixed l`，下一步需要补的是 `loss` 后缀，而不是继续扩大无差别 target-only memory。

## 关键新增文件

- `src/minigpt/bounded_objective_loss_signal_bridge_target_only_memory_partial_hit_diagnostic.py`
  - v875 核心诊断模块。
  - 读取 v874 replay comparison。
  - 将每条 replay row 分类为 `fixed_with_loss_prefix`、`fixed_only`、`loss_only`、`zero_hit` 等。
  - 汇总 `fixed_without_loss_case_count`、`loss_prefix_case_count`、`loss_hit_case_count`。
  - 生成 root causes 和下一步 patch 指令。

- `src/minigpt/bounded_objective_loss_signal_bridge_target_only_memory_partial_hit_diagnostic_artifacts.py`
  - 输出 JSON、CSV、TXT、Markdown、HTML。
  - HTML 展示 Case Diagnostics 和 Root Causes。

- `scripts/diagnose_bounded_objective_loss_signal_bridge_target_only_memory_partial_hit.py`
  - CLI 入口。
  - 支持 `--replay-comparison`、`--out-dir`、`--require-diagnostic-ready`、`--force`。

- `tests/test_bounded_objective_loss_signal_bridge_target_only_memory_partial_hit_diagnostic.py`
  - 覆盖 loss suffix gap、无 partial hit 时失败、writer 和 CLI。

## 核心分类逻辑

v875 的 `_case_diagnostic()` 关注三个信号：

```text
hit_terms contains fixed
hit_terms contains loss
continuation contains los or endswith " l"
```

如果一条 case 命中了 `fixed`，没命中 `loss`，但 continuation 已经出现 `loss` 前缀，就归类为：

```text
fixed_with_loss_prefix
```

v874 的三条真实输出都是这个模式：

```text
canonical_direct_completion -> "\nfixed l"
minimal_direct_completion   -> "\nfixed l"
completion_label_surface    -> "fixed l"
```

所以诊断汇总为：

```text
fixed_without_loss_case_count=3
loss_prefix_case_count=3
loss_hit_case_count=0
all_cases_loss_prefix=True
```

## Root causes

v875 生成四个 root causes：

- `loss_suffix_uptake_gap`
  - 三条 case 都到达了 `fixed` 和 `loss` 前缀，但没有完整输出 `loss`。

- `fixed_dominates_required_pair`
  - target-only memory 强化了 `fixed`，但 `fixed loss` 的 pair 还不稳定。

- `no_anchor_partial_signal`
  - 这个 partial-hit 是无 decoder anchor 的真实信号，下一步应优先继续数据级修补。

- `partial_signal_without_contract_pass`
  - 有改进，但仍无 pass case，不能 promotion。

## 真实诊断命令

```text
python -B scripts/diagnose_bounded_objective_loss_signal_bridge_target_only_memory_partial_hit.py
  --replay-comparison e/874/解释/bounded-objective-loss-signal-bridge-target-only-memory-replay-comparison
  --out-dir e/875/解释/bounded-objective-loss-signal-bridge-target-only-memory-partial-hit-diagnostic
  --require-diagnostic-ready
  --force
```

输出：

```text
decision=bounded_objective_loss_signal_bridge_target_only_memory_partial_hit_loss_suffix_gap
partial_case_count=3
fixed_without_loss_case_count=3
loss_prefix_case_count=3
loss_hit_case_count=0
model_quality_claim=fixed_prefix_recovered_loss_suffix_missing
next_action=build_bounded_objective_loss_signal_bridge_target_only_memory_loss_suffix_patch
```

## 测试覆盖

focused 测试：

```text
python -m pytest tests/test_bounded_objective_loss_signal_bridge_target_only_memory_partial_hit_diagnostic.py -q -o cache_dir=runs/pytest-cache-v875-focus
```

结果：

```text
3 passed
```

测试保护：

- 三条 `fixed l` 必须识别为 loss suffix gap。
- 没有 partial hit 时诊断必须失败。
- writer 和 CLI 必须输出 JSON、CSV、TXT、Markdown、HTML。

## 运行证据

- 解释目录：`e/875/解释/bounded-objective-loss-signal-bridge-target-only-memory-partial-hit-diagnostic/`
- 截图目录：`e/875/图片/`
- Playwright MCP 截图：`e/875/图片/v875-bounded-objective-loss-signal-bridge-target-only-memory-partial-hit-diagnostic-html.png`

## 一句话总结

v875 把 target-only memory 路线的进展和瓶颈同时钉住：`fixed` 已恢复，`loss` 后缀仍缺失，下一版应做窄口径 loss-suffix patch。
