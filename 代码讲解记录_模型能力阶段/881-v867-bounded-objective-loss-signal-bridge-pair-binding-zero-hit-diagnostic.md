# v867：bounded objective loss signal bridge pair-binding zero-hit diagnostic

## 本版目标和边界

v867 的目标是解释 v866 的 zero-hit 回退。v866 显示 v865 pair-binding checkpoint 在三个 bounded objective cases 上全部没有命中 `fixed` 或 `loss`，continuation 反而是 `answer:` / `ans`。

本版不再训练，也不修改 contract。它只读 v866 replay rows，判断 zero-hit 的具体形态。

边界：

- 不训练。
- 不 replay 新 checkpoint。
- 不 promotion。
- 不使用 decoder anchor。
- 不把 zero-hit 说成能力提升。

## 前置链路

```text
v864 pair-binding patch
 -> v865 pair-binding training run
 -> v866 pair-binding replay zero-hit
 -> v867 zero-hit diagnostic
```

v867 是一次负结果诊断：它帮助决定下一步修数据格式，而不是继续盲目加训练步数。

## 关键新增文件

- `src/minigpt/bounded_objective_loss_signal_bridge_pair_binding_zero_hit_diagnostic.py`
  - 核心诊断模块。
  - 读取 v866 replay comparison。
  - 判断 continuation 是否为 `answer:`、`ans`、`completion:` 这类 label echo。
  - 输出 root causes 和下一步建议。

- `src/minigpt/bounded_objective_loss_signal_bridge_pair_binding_zero_hit_diagnostic_artifacts.py`
  - 输出 JSON、CSV、TXT、Markdown、HTML。

- `scripts/diagnose_bounded_objective_loss_signal_bridge_pair_binding_zero_hit.py`
  - CLI 入口。
  - 支持 `--replay-comparison`、`--out-dir`、`--require-diagnostic-ready`、`--force`。

- `tests/test_bounded_objective_loss_signal_bridge_pair_binding_zero_hit_diagnostic.py`
  - 覆盖 label echo zero-hit、非 zero-hit 阻断、writer 和 CLI。

- `e/867/解释/bounded-objective-loss-signal-bridge-pair-binding-zero-hit-diagnostic/`
  - v867 真实诊断证据。

- `e/867/图片/v867-bounded-objective-loss-signal-bridge-pair-binding-zero-hit-diagnostic-html.png`
  - Playwright MCP 截图。

## 诊断规则

v867 对每个 replay row 读取：

```text
case_id
continuation
hit_terms
missed_terms
case_pass
any_hit
```

然后把 continuation 归一化：

```text
normalized = " ".join(continuation.lower().split())
```

如果 continuation 以这些标签开头：

```text
answer
ans
completion
```

就判为：

```text
label_echo=True
```

本版的关键判断是：

```text
all_cases_label_echo=True
```

这说明模型把输出预算消耗在 prompt 标签上，而不是输出目标词。

## 真实诊断结果

命令：

```text
python -B scripts/diagnose_bounded_objective_loss_signal_bridge_pair_binding_zero_hit.py
  --replay-comparison e/866/解释/bounded-objective-loss-signal-bridge-pair-binding-replay-comparison
  --out-dir e/867/解释/bounded-objective-loss-signal-bridge-pair-binding-zero-hit-diagnostic
  --require-diagnostic-ready
  --force
```

输出：

```text
status=pass
decision=bounded_objective_loss_signal_bridge_pair_binding_zero_hit_label_echo
case_count=3
label_echo_case_count=3
zero_hit_case_count=3
all_cases_label_echo=True
model_quality_claim=label_echo_regression
next_action=build_single_line_completion_surface_patch
```

case 级别：

```text
canonical_direct_completion -> answer:
minimal_direct_completion   -> answer:
completion_label_surface    -> ans
```

## Root causes

v867 识别四个原因：

```text
label_echo_over_target_terms
partial_signal_regressed_to_zero_hit
no_anchor_failure_needs_surface_repair
short_decode_label_fragment
```

其中最关键的是：

```text
label_echo_over_target_terms
```

它说明当前 pair-binding patch 的多行结构可能强化了标签表面，而不是让模型直接输出 `fixed loss`。

## 下一步为什么是 single-line surface patch

继续追加同类样本可能会继续强化：

```text
answer:
completion:
```

所以 v868 更合理的方向是构建 single-line completion surface patch，把训练目标改成更短、更直接的形式：

```text
answer: fixed loss
completion: fixed loss
target: fixed loss
```

并减少这种多行结构：

```text
answer:
fixed
loss
```

## 测试覆盖

focused pytest 覆盖：

- label echo zero-hit：
  - 三个 case 都是 `answer:` / `ans`。
  - 诊断必须 ready，并输出 `label_echo_over_target_terms`。

- 非 zero-hit 阻断：
  - `any_hit_case_count=1` 时不能误用 zero-hit diagnostic。

- writer + CLI：
  - locate、JSON/CSV/TXT/Markdown/HTML 输出和 CLI wiring。

```text
3 passed
```

## 运行证据

产物：

```text
e/867/解释/bounded-objective-loss-signal-bridge-pair-binding-zero-hit-diagnostic/
```

截图：

```text
e/867/图片/v867-bounded-objective-loss-signal-bridge-pair-binding-zero-hit-diagnostic-html.png
```

Playwright MCP snapshot 确认：

```text
Status=pass
Decision=bounded_objective_loss_signal_bridge_pair_binding_zero_hit_label_echo
Label echo=3
Zero hit=3
All echo=True
Claim=label_echo_regression
```

## 一句话总结

v867 证明 pair-binding route 的失败形态是 label echo regression，下一步应修 prompt surface，而不是继续堆同类 pair-binding 训练。
