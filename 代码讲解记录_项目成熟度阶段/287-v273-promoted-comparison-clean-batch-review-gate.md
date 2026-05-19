# v273 promoted comparison clean batch review gate

## 本版目标和边界

v273 的目标是把 v272 已经写入 promotion index 的 clean batch-review guard 继续带到 promoted training-scale comparison。此前 index 层已经能把不满足 clean requirement 的 promotion 排除出 compare inputs，但 promoted comparison 仍需要自己重检这些字段，避免旧 index、手工 index 或未来兼容输入绕过比较层。

本版不改变：

- training scale run comparison 的分数和 delta 计算；
- promoted comparison 的 baseline 选择语义；
- suite consistency guard；
- selected batch review/blocker 的既有传播字段；
- promoted rows 的可见性。

因此，dirty clean-required promotion 不会消失。它仍保留在 promoted input table 里，但不会进入真正比较的 run 列表。

## 前置链路

v268 把 `require_clean_batch_review` 加到 standalone run decision。v269 接入 workflow。v270 接入 execution handoff。v271 接入 promotion acceptance。v272 接入 promotion index。v273 是 promoted comparison 层的防漏网：只有 clean requirement 满足的 promoted input 才能被送入模型能力对比。

## 关键文件

### `src/minigpt/promoted_training_scale_comparison.py`

`_promotion_rows()` 新增 `_clean_batch_review_guard()` 读取：

- `clean_batch_review_guard.handoff_require_clean_batch_review`
- `clean_batch_review_guard.handoff_clean_batch_review_status`
- `summary.handoff_require_clean_batch_review`
- `summary.handoff_clean_batch_review_status`

如果 `handoff_require_clean_batch_review == true` 且状态不是 `clean`，本版会把该行的 `promoted_for_comparison` 改为 `False`。这意味着它仍是 promotion row，但不再进入 `compare_rows`。

summary 新增：

- `handoff_require_clean_batch_review_count`
- `handoff_clean_batch_review_count`
- `handoff_unclean_batch_review_count`
- `comparison_ready_handoff_require_clean_batch_review_count`
- `comparison_ready_handoff_clean_batch_review_count`
- `comparison_ready_handoff_unclean_batch_review_count`

recommendations 也会优先提示 unclean clean-required handoff，因为这种情况比普通 batch review/blocker 更接近“证据不能进入模型质量比较”的硬边界。

### `src/minigpt/promoted_training_scale_comparison_artifacts.py`

CSV 新增 row 字段：

- `handoff_require_clean_batch_review`
- `handoff_clean_batch_review_status`

Markdown 和 HTML 新增 summary 展示：

- handoff clean-required、clean、unclean counts；
- comparison-ready clean-required、clean、unclean counts。

Promoted Inputs 表新增 `Clean Required` 和 `Clean Status` 两列，让读报告的人能解释为什么某个 promoted row 没有进入 compared runs。

### `scripts/compare_promoted_training_scale_runs.py`

CLI 输出新增 clean batch-review counts，自动化日志可以直接看到 comparison 层最终消费了多少 clean-required 输入、挡掉了多少 unclean 输入。

### `tests/test_promoted_training_scale_comparison.py`

新增 clean batch-review 场景：

- `alpha` 是 promoted 且 clean-required clean，进入比较；
- `beta` 是 promoted 但 clean-required review，保留在 promoted rows，排除出比较；
- `gamma` 是 promoted 且不要求 clean batch-review，进入比较。

测试断言：

- compared runs 只有 `alpha` 和 `gamma`；
- summary clean-required/clean/unclean counts 正确；
- comparison-ready unclean count 为 0；
- CSV、Markdown、HTML 和 CLI stdout 都含有新增字段。

## 输入输出

输入 promotion row 示例：

```json
{
  "promotion_status": "promoted",
  "promoted_for_comparison": true,
  "clean_batch_review_guard": {
    "handoff_require_clean_batch_review": true,
    "handoff_clean_batch_review_status": "review"
  }
}
```

v273 输出时保留该 row，但把它变成：

```json
{
  "promotion_status": "promoted",
  "promoted_for_comparison": false,
  "handoff_require_clean_batch_review": true,
  "handoff_clean_batch_review_status": "review"
}
```

如果同一个 index 中还有至少两个可比较输入，comparison 继续执行；否则返回 blocked report。

## 测试覆盖

- promoted comparison 聚焦测试覆盖 clean guard 读取、dirty input 排除、artifact 渲染和 CLI 输出。
- 全量 unittest 覆盖训练规模治理、报告工具、服务端、UI、发布治理和数据治理模块。
- source encoding hygiene 确认新增源文件无 BOM、无语法错误、无兼容性错误。
- smoke 运行真实脚本，证明 dirty clean-required promoted input 被挡在 compared runs 之外。

## 证据归档

运行截图和解释归档在 `c/273`：

- `c/273/图片/01-focused-tests.png`
- `c/273/图片/02-promoted-comparison-clean-batch-gate-smoke.png`
- `c/273/图片/03-full-unittest.png`
- `c/273/图片/04-source-encoding.png`
- `c/273/图片/05-promoted-comparison-html.png`
- `c/273/图片/06-docs-check.png`
- `c/273/解释/说明.md`

## 一句话总结

v273 让 promoted training-scale comparison 自己具备 clean batch-review 防漏网能力，避免不干净 promotion evidence 被误当成模型能力对比证据。
