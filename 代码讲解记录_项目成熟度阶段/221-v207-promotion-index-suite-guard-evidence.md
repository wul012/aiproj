# v207 promotion index suite guard evidence 代码讲解

## 本版目标

v207 的目标是把 v206 已经进入 promotion acceptance 的 suite guard evidence，再往上游一步带到 training-scale promotion index。

v206 让单个 promotion report 能保留 `handoff_require_suite_consistency`、`handoff_suite_consistency`、`handoff_suite_mismatch_count` 和 `handoff_selected_suite_path`，但多个 promotion 汇总成 index 之后，这条 handoff suite boundary 仍然会在索引层变弱：index 能筛 promoted 输入、生成 compare command，却没有把每个 promotion 继承来的 suite 边界一起展示出来。

本版补上这一步，让 promotion index 不只告诉人“哪些 promoted 结果可以比较”，还告诉人“这些 promoted 结果各自继承的 handoff suite 边界是什么”。

## 不做什么

本版不重新计算 suite consistency，不改变 promotion 状态，不改变 compare-ready 选择规则，也不把 suite guard 变成新的 index 阻断条件。

suite consistency 的计算仍然属于 comparison/decision/workflow/handoff/promotion 的上游链路。index 这里只做证据汇总和展示，让 compare-ready 的 promoted 输入保留来自 handoff 的 suite evidence。

## 前置路线

v202-v206 已经把 suite consistency、strict decision guard、workflow handoff 和 promotion acceptance 串起来了。

v185 之前的 training scale promotion index 只有 helper split 和 promoted compare-ready 选择，更多是一个索引层入口。v207 在这个入口上补上 suite guard evidence，形成：

```text
comparison -> decision -> workflow -> handoff -> promotion -> promotion index
```

这条路线很重要，因为索引层是后续 `compare_training_scale_runs.py` 的入口，属于“是否进入跨 run 比较”的门口，而不是单纯的报告尾页。

## `src/minigpt/training_scale_promotion_index_helpers.py`

### `_promotion_row()`

这个 helper 现在会读取 promotion report 顶层的 `suite_guard`，并把以下字段放进每一行 promotion row：

```python
"handoff_require_suite_consistency"
"handoff_suite_consistency"
"handoff_suite_mismatch_count"
"handoff_selected_suite_path"
```

这里没有自己重新计算 suite 结果，而是把 promotion 层已经继承到的 handoff suite evidence 再透传一层，方便 index 汇总。

### `_suite_guard()`

`_suite_guard()` 做的是兼容性读取：

1. 优先读 `report["suite_guard"]`
2. 其次读 `report["summary"]`

同时兼容：

- `handoff_require_suite_consistency` / `require_suite_consistency`
- `handoff_suite_consistency` / `suite_consistency`
- `handoff_suite_mismatch_count` / `suite_mismatch_count`
- `handoff_selected_suite_path` / `selected_suite_path`

这让 index 可以吃到 v206 风格的 promotion evidence，也能兼容更旧或更平铺的 summary 写法。

### `_summary()`

index summary 新增四个计数：

```python
handoff_require_suite_consistency_count
handoff_suite_consistent_count
handoff_suite_mismatch_total
handoff_selected_suite_path_count
```

这些不是新的治理判断，而是把索引中有多少条 promotion 保留了 suite guard 边界展示出来。这样一眼就能看出 index 是否真的在携带 clean-comparison 证据，而不是只在看 promoted 名单。

## `src/minigpt/training_scale_promotion_index.py`

### CSV 输出

CSV 新增四列：

```text
handoff_require_suite_consistency
handoff_suite_consistency
handoff_suite_mismatch_count
handoff_selected_suite_path
```

### Markdown 输出

Markdown summary 新增四条统计：

```text
Handoff strict suite
Handoff suite consistent
Handoff suite mismatches
Selected suite references
```

Promotions 表也新增 suite 相关列，方便人工直接看每个 promoted 输入的 handoff 边界，而不用再单独打开 promotion report。

### HTML 输出

HTML stats 和 promotions table 也同步加入 suite guard 相关字段。这一点很关键，因为 index 的常见消费场景就是浏览器打开 HTML 直接扫可比较输入；如果 HTML 没有这几列，suite boundary 就只存在于 JSON，人工复核会断掉。

## `scripts/index_training_scale_promotions.py`

CLI 本身没有变成新的治理决策器，它还是：

1. 读取 promotion JSON 或 promotion 目录
2. 构建 promotion index
3. 写出 JSON/CSV/Markdown/HTML

本版只是让它在 stdout 里额外打印 suite guard 统计，便于 smoke 和 CI 直接确认这条证据被读到了。

## 测试覆盖

`tests/test_training_scale_promotion_index.py` 新增了两类保护：

1. 构造带 `suite_guard` 的 promoted promotion，确认 index row 和 summary 都能收到 handoff suite evidence。
2. 通过 CLI smoke 运行 `scripts/index_training_scale_promotions.py`，确认 stdout 和输出文件都包含 suite guard 统计与 HTML 产物。

原来的 compare-input、baseline、HTML escape、helper contract 测试继续保护 promoted selection 语义没有被破坏。

## 运行证据

本版运行证据归档在 `c/207`：

- `图片/01-training-scale-promotion-index-tests.png`
- `图片/02-training-scale-promotion-index-smoke.png`
- `图片/03-training-scale-promotion-index-artifact-smoke.png`
- `图片/04-source-encoding-smoke.png`
- `图片/05-full-unittest.png`
- `图片/06-docs-check.png`

这组证据的角色是：

1. tests 图证明 index schema 和 suite guard 透传逻辑成立。
2. smoke 图证明 CLI 真的能把 promoted promotion 汇总成 compare-ready index。
3. artifact 图证明 JSON/CSV/Markdown/HTML 四种输出都携带 suite boundary。
4. source encoding 和 full unittest 证明这不是局部修补，而是仓库级稳定状态。
5. docs check 证明 README、`c/207` 和讲解目录已经对齐。

## 证据链角色

v207 的位置不是再向外扩模型能力，而是把治理证据从单个 promotion report 再往上游汇总一步：

```text
workflow -> handoff -> promotion -> promotion index
```

这样 compare-ready 的索引不仅是 promoted 列表，也是一份保留 handoff suite boundary 的选择面。

## 一句话总结

v207 把 handoff suite guard 再往上游推进到 promotion index，让 compare-ready promoted 输入也保留 clean-comparison 边界。
