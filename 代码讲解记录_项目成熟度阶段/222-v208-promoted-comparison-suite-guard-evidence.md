# v208 promoted comparison suite guard evidence 代码讲解

## 本版目标

v208 的目标是把 v207 已经进入 training-scale promotion index 的 handoff suite guard evidence，继续带到 promoted training-scale comparison。

v207 让 index 能看见每个 promotion 继承来的 `handoff_require_suite_consistency`、`handoff_suite_consistency`、`handoff_suite_mismatch_count` 和 `handoff_selected_suite_path`。但 promoted comparison 是后续选择 baseline 前真正要阅读的比较报告，如果这一步只保留真实 run comparison 的 suite path，却丢掉 index 层的 handoff suite guard，人工复核时仍然需要回翻 index。

本版补上这一步，让 promoted-only comparison 同时回答两个问题：

1. 这些 promoted runs 的真实比较结果是什么。
2. 这些 promoted inputs 从 promotion index 继承的 handoff suite boundary 是什么。

## 不做什么

本版不重新计算 suite consistency，不改变 promoted-only comparison 的输入筛选规则，不改变 baseline 选择，不改变 readiness score，也不新增阻断条件。

真实 run 之间是否 mixed-suite 仍由 `training_scale_run_comparison.py` 根据 scale run 的 `suite_path` 计算。v208 只是把 promotion index 里已有的 handoff suite guard 字段继续透传到 promoted comparison 的 row、summary、artifact 和 CLI 输出。

## 前置路线

v202-v207 已经形成了这条 suite evidence chain：

```text
training-scale comparison -> decision -> workflow -> handoff -> promotion -> promotion index
```

v208 把链路再往 baseline selection 前推进一层：

```text
promotion index -> promoted comparison
```

这一步的价值在于 promoted comparison 是 `decide_promoted_training_scale_baseline.py` 的上游输入。它不应该只知道“哪些 runs 被比较了”，也应该保留这些 runs 在 promotion index 里对应的 handoff suite guard。

## `src/minigpt/promoted_training_scale_comparison.py`

### `_promotion_rows()`

`_promotion_rows()` 从 promotion index 的 `promotions` 里读取 promoted 输入。v208 为每一行新增四个字段：

```python
"handoff_require_suite_consistency"
"handoff_suite_consistency"
"handoff_suite_mismatch_count"
"handoff_selected_suite_path"
```

这些字段不是从 scale run 重新推导出来的，而是来自 promotion index。这样 promoted comparison 的输入行能保留 index 的 review context。

### `_summary()`

summary 新增五个统计：

```python
handoff_require_suite_consistency_count
handoff_suite_consistent_count
handoff_suite_mismatch_total
handoff_selected_suite_path_count
comparison_ready_handoff_suite_mismatch_total
```

前四个字段说明整个 promoted comparison 报告里有多少 promotion rows 保留了 suite guard evidence；最后一个字段只看 `promoted_for_comparison=True` 的输入，方便确认真正参与比较的 promoted runs 是否还有 handoff mismatch。

这里依然不改变 `comparison_status`。如果 promoted runs 真实 suite path mixed，仍由 comparison summary 的 `suite_consistency` 和 `suite_mismatch_count` 表达；handoff 字段是上游边界证据。

## `src/minigpt/promoted_training_scale_comparison_artifacts.py`

### CSV 输出

CSV 新增四列：

```text
handoff_require_suite_consistency
handoff_suite_consistency
handoff_suite_mismatch_count
handoff_selected_suite_path
```

这让自动消费方能直接从 promoted comparison CSV 看见 promotion-index handoff guard，而不用再 join promotion index。

### Markdown 输出

Markdown summary 新增：

```text
Handoff strict suite
Handoff suite consistent
Handoff suite mismatches
Comparison-ready handoff suite mismatches
```

Promoted Inputs 表新增 handoff suite、mismatch 和 selected suite 三列，便于人工审阅。

### HTML 输出

HTML stats 和 promoted inputs table 同步展示 handoff suite guard 字段。HTML 是最常用的人眼复核入口，所以这一步让 suite boundary 不只存在于 JSON/CSV。

## `scripts/compare_promoted_training_scale_runs.py`

CLI stdout 新增 handoff suite guard 统计：

```text
handoff_require_suite_consistency_count
handoff_suite_consistent_count
handoff_suite_mismatch_total
comparison_ready_handoff_suite_mismatch_total
```

这让 smoke 和 CI 可以不用解析 HTML，就能确认 promoted comparison 真的消费到了 index 层 suite guard。

## 测试覆盖

`tests/test_promoted_training_scale_comparison.py` 新增 `test_carries_index_handoff_suite_guard_into_outputs_and_script`。

这个测试构造两个带 handoff suite guard 的 promoted index inputs，然后覆盖三件事：

1. `build_promoted_training_scale_comparison()` 的 row 和 summary 都携带 suite guard 字段。
2. JSON/CSV/Markdown/HTML 输出能看到这些字段。
3. CLI smoke 能完成 promoted-only comparison，并在 stdout 打印 handoff suite guard 统计。

原有测试继续保护 promoted-only 输入筛选、mixed suite summary、insufficient input blocking、invalid baseline blocking 和 HTML escape，不让 v208 的证据字段改变原有比较语义。

## 运行证据

本版运行证据归档在 `c/208`：

- `图片/01-promoted-training-scale-comparison-tests.png`
- `图片/02-promoted-training-scale-comparison-smoke.png`
- `图片/03-promoted-comparison-artifact-suite-guard-smoke.png`
- `图片/04-source-encoding-smoke.png`
- `图片/05-full-unittest.png`
- `图片/06-docs-check.png`

这些证据分别证明：聚焦测试通过、CLI comparison 能跑通、四类 artifact 都带字段、source encoding 仍干净、全量 unittest 通过、README 和归档说明已经对齐。

## 证据链角色

v208 处在 promotion index 和 promoted baseline decision 之间。它让 promoted comparison 成为一个更完整的 review packet：既包含真实 run comparison，也包含 promotion index 继承来的 suite guard context。

## 一句话总结

v208 把 promotion-index handoff suite guard 接到 promoted-only comparison，让 baseline 选择前的比较报告继续保留 clean-comparison 边界。
