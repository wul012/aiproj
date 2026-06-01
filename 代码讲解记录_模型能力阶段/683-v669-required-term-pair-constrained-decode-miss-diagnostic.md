# v669 required-term pair constrained decode miss diagnostic

## 本版目标和边界

v669 给 v667 的 constrained decode feasibility 补一层 miss diagnostic。目标是解释为什么 constrained decode 只有 partial gain，以及下一步应该修哪一侧。

本版不训练新模型，不修改 checkpoint，也不把 decode-only partial gain 宣称为模型能力提升。

## 前置链路

v667 对 v630 generation anchor 跑 constrained decode：

- default profile 没有命中 fixed/loss。
- block competing initial profile 命中 loss。
- fixed 仍未命中。

v669 读取这份 report，把 case rows 转成可审计的 miss class。

## 关键新增文件

### `src/minigpt/model_capability_required_term_pair_constrained_decode_miss_diagnostic.py`

核心 builder 是 `build_model_capability_required_term_pair_constrained_decode_miss_diagnostic()`。

它读取 constrained decode feasibility report，生成：

- `diagnostic_rows`: 每个 term/profile 的 hit 状态、blocked token、continuation preview、miss class。
- `summary`: fixed/loss constrained hit、remaining missed terms、recommended next route。
- `interpretation`: 说明下一步是否应继续 decode、promote profile，还是回到 objective design。

本版最重要的分类是：

- `prefix_fragment_without_full_term`: continuation 出现了目标前缀片段，但没有完整 required term。

这正好对应 v667 的 fixed 侧：输出里有 `fix` 片段，但没有完整 `fixed` 命中。

### `src/minigpt/model_capability_required_term_pair_constrained_decode_miss_diagnostic_artifacts.py`

负责 JSON/CSV/text/Markdown/HTML 输出。HTML 报告展示 metric cards、diagnostic rows 和 next action，方便截图归档。

### `scripts/run_model_capability_required_term_pair_constrained_decode_miss_diagnostic.py`

新增 CLI：

```powershell
python -B scripts\run_model_capability_required_term_pair_constrained_decode_miss_diagnostic.py <feasibility-report-or-dir> --out-dir <dir> --require-pass --force
```

## 运行结果

本版读取：

```text
e/667/解释/model-capability-required-term-pair-v630-constrained-decode-feasibility
```

输出：

- `decision=fixed_branch_still_missed_after_constrained_decode`
- `fixed_constrained_hit=False`
- `loss_constrained_hit=True`
- `fixed_miss_class=prefix_fragment_without_full_term`
- `remaining_missed_terms=fixed`
- `recommended_next_route=explicit_dual_objective_boundary_for_fixed_retention`

## 测试覆盖

新增测试文件：

```text
tests/test_model_capability_required_term_pair_constrained_decode_miss_diagnostic.py
```

覆盖内容：

- fixed miss + loss hit 时路由到 explicit dual-objective boundary。
- pair-full decode 时没有 miss。
- 缺少 constrained fixed case 时失败。
- 五种 artifact 格式可渲染。
- locator 支持输出目录。

运行结果：`5 passed`。

## 证据归档

- JSON/CSV/text/Markdown/HTML: `e/669/解释/model-capability-required-term-pair-v630-constrained-decode-miss-diagnostic/`
- 截图: `e/669/图片/v669-constrained-decode-miss-diagnostic.png`
- 解释: `e/669/解释/说明.md`

一句话总结：v669 把 constrained decode 的 partial gain 拆成明确的 fixed-side miss，为下一步 explicit dual-objective boundary 提供证据。
