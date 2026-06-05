# v871：bounded objective loss signal bridge single-line surface zero-hit diagnostic

## 本版目标和边界

v871 的目标是解释 v870 的 zero-hit replay。v870 显示 v869 checkpoint 虽然 `final_val_loss=0.8147876858711243`，但在 unchanged v836 objective contract 上仍然 `any_hit_case_count=0`。这意味着训练 loss 下降没有转换成目标能力。

本版不训练，不修改 contract，也不构造新 patch。它只读 v870 replay comparison，诊断 continuation 的失败形态，并给 v872 提供可行动方向。

边界：

- 不把 low loss 解释成能力提升。
- 不把 zero-hit 混同为普通失败。
- 不使用 decoder anchor。
- 不直接开始下一轮训练。

## 前置链路

```text
v868 single-line surface patch
 -> v869 single-line surface training run
 -> v870 single-line surface replay zero-hit
 -> v871 zero-hit diagnostic
```

v871 是单行修补路线的失败解释层。它回答的问题是：为什么改成 single-line surface 后，模型仍没有输出 `fixed` 或 `loss`？

## 关键新增文件

- `src/minigpt/bounded_objective_loss_signal_bridge_single_line_surface_zero_hit_diagnostic.py`
  - 核心诊断模块。
  - 读取 v870 replay comparison。
  - 分类 continuation，并识别 label echo、label prefix fragment 和 loss-without-uptake。

- `src/minigpt/bounded_objective_loss_signal_bridge_single_line_surface_zero_hit_diagnostic_artifacts.py`
  - 输出 JSON、CSV、TXT、Markdown、HTML。
  - CSV 记录每个 case 的 continuation class、echo/fragment 标记和 missed terms。

- `scripts/diagnose_bounded_objective_loss_signal_bridge_single_line_surface_zero_hit.py`
  - CLI 入口。
  - 支持 `--replay-comparison`、`--out-dir`、`--require-diagnostic-ready`、`--force`。

- `tests/test_bounded_objective_loss_signal_bridge_single_line_surface_zero_hit_diagnostic.py`
  - 覆盖真实失败形态、非 zero-hit 阻断、writer 和 CLI。

- `e/871/解释/bounded-objective-loss-signal-bridge-single-line-surface-zero-hit-diagnostic/`
  - v871 真实诊断证据。

- `e/871/图片/v871-bounded-objective-loss-signal-bridge-single-line-surface-zero-hit-diagnostic-html.png`
  - Playwright MCP 截图证据。

## 核心分类

v871 对 continuation 做归一化：

```text
normalized = " ".join(continuation.lower().split())
```

然后分成：

```text
exact_label_echo
label_prefix_fragment
empty
non_target_fragment
```

真实 v870 中：

```text
answer:  -> exact_label_echo
answer:  -> exact_label_echo
answeti  -> label_prefix_fragment
```

这说明失败仍在标签面附近打转，而不是靠近 `fixed loss`。

## Root cause 设计

v871 会输出多条 root cause：

```text
label_echo_persisted_after_single_line_patch
answer_label_echo_still_dominant
completion_label_fragment
loss_improved_without_required_term_uptake
no_anchor_surface_failure
short_decode_budget_consumed_by_label
```

最重要的是：

```text
loss_improved_without_required_term_uptake
```

它明确区分训练指标和任务能力：v869 的 loss 下降是真实的，但 v870 replay 没有任何 `fixed` 或 `loss` 命中。

## 真实诊断命令

```text
python -B scripts/diagnose_bounded_objective_loss_signal_bridge_single_line_surface_zero_hit.py
  --replay-comparison e/870/解释/bounded-objective-loss-signal-bridge-single-line-surface-replay-comparison
  --out-dir e/871/解释/bounded-objective-loss-signal-bridge-single-line-surface-zero-hit-diagnostic
  --require-diagnostic-ready
  --force
```

输出：

```text
status=pass
decision=bounded_objective_loss_signal_bridge_single_line_surface_zero_hit_label_echo_persisted
case_count=3
exact_label_echo_case_count=2
label_prefix_fragment_case_count=1
zero_hit_case_count=3
loss_improved_without_required_term_uptake=True
model_quality_claim=label_echo_persisted_after_single_line_training
next_action=build_target_only_completion_memory_patch
```

## 测试覆盖

focused 测试：

```text
python -m pytest tests/test_bounded_objective_loss_signal_bridge_single_line_surface_zero_hit_diagnostic.py -q -o cache_dir=runs/pytest-cache-v871-focus
```

结果：

```text
3 passed
```

测试保护三件事：

- 能识别 2 个 exact label echo 和 1 个 label-prefix fragment。
- 非 zero-hit replay 不能误走 zero-hit diagnostic。
- writer 和 CLI 能输出 JSON、CSV、TXT、Markdown、HTML。

## 运行证据

- 解释目录：`e/871/解释/bounded-objective-loss-signal-bridge-single-line-surface-zero-hit-diagnostic/`
- 截图目录：`e/871/图片/`
- Playwright MCP 截图：`e/871/图片/v871-bounded-objective-loss-signal-bridge-single-line-surface-zero-hit-diagnostic-html.png`

## 一句话总结

v871 证明 single-line surface 训练仍停留在标签回声和标签碎片，下一版应转向 target-only completion memory patch，用更少标签、更强目标答案记忆来尝试打破回声。
