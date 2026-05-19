# v272 promotion index clean batch review gate

## 本版目标和边界

v272 的目标是把 promotion clean batch-review evidence 带到 training-scale promotion index。此前 v271 已经能在 promotion acceptance 阶段阻断不满足 handoff clean batch-review requirement 的报告，但 promotion index 仍需要独立保留这条 guard，尤其要防止旧报告或手工报告把不干净的 promotion 标成 `promoted` 后进入 compare inputs。

本版不改变：

- promotion report 的生成规则；
- 已满足 clean requirement 的 promoted run 进入 compare inputs 的规则；
- suite guard 计数和推荐语义；
- compare command 的格式；
- 下游 promoted comparison 的输入文件结构。

## 前置链路

v268 将 `require_clean_batch_review` 加入 run decision。v269 接入 workflow。v270 接入 execution handoff。v271 接入 promotion acceptance。v272 是索引层的防漏网：它不只展示 promotion status，还检查 handoff clean batch-review requirement 是否满足，然后再决定 promotion 是否可以作为 comparison input。

## 关键文件

### `src/minigpt/training_scale_promotion_index_helpers.py`

新增 `_clean_batch_review_guard()`，从 promotion summary 和 `clean_batch_review_guard` 中读取：

- `handoff_require_clean_batch_review`
- `handoff_clean_batch_review_status`

`_promotion_row()` 现在会计算 `clean_requirement_satisfied`。只有当：

- `promotion_status == "promoted"`；
- scale run JSON 存在；
- 没有 clean requirement，或 clean status 为 `clean`；

该 promotion 才会被标记为 `promoted_for_comparison=True`。

summary 新增：

- `handoff_require_clean_batch_review_count`
- `handoff_clean_batch_review_count`
- `handoff_unclean_batch_review_count`

recommendations 在存在 unclean clean-required promotion 时，会优先提示先解决 handoff clean batch-review requirement。

### `src/minigpt/training_scale_promotion_index.py`

CSV、Markdown、HTML 都新增展示：

- row 级 `handoff_require_clean_batch_review`
- row 级 `handoff_clean_batch_review_status`
- summary 级 clean-required/clean/unclean counts

这让 index 报告本身能够解释为什么某个 promotion 虽然是 `promoted`，但没有进入 compare inputs。

### `scripts/index_training_scale_promotions.py`

CLI 输出新增：

```text
handoff_require_clean_batch_review_count=<n>
handoff_clean_batch_review_count=<n>
handoff_unclean_batch_review_count=<n>
```

自动化日志可以直接看到 index 是否排除了 unclean required promotions。

### `tests/test_training_scale_promotion_index.py`

新增覆盖：

- clean requirement 满足时，promoted promotions 仍进入 compare inputs；
- clean requirement 未满足时，即使 promotion status 是 `promoted`，也会被排除出 compare inputs；
- CSV/Markdown/HTML 和 CLI stdout 都展示新增字段。

## 输入输出

输入是一个或多个 `training_scale_promotion.json` 或 promotion 目录。新增消费字段示例：

```json
{
  "summary": {
    "handoff_require_clean_batch_review": true,
    "handoff_clean_batch_review_status": "review"
  }
}
```

输出 index report 新增：

```json
{
  "summary": {
    "comparison_ready_count": 1,
    "handoff_require_clean_batch_review_count": 2,
    "handoff_clean_batch_review_count": 1,
    "handoff_unclean_batch_review_count": 1
  }
}
```

## 测试覆盖

- promotion index 聚焦测试覆盖 clean guard 汇总、compare input 排除、artifact 渲染和 CLI 输出。
- 相关 promotion 测试一起运行，保护 v271 acceptance 语义。
- 全量 unittest 保护训练规模链路、报告工具、UI、发布治理和数据治理模块。
- source encoding hygiene 检查保证新增代码和文档没有 BOM 或语法错误。

## 证据归档

运行截图和解释归档在 `c/272`：

- `c/272/图片/01-focused-tests.png`
- `c/272/图片/02-index-clean-batch-gate-smoke.png`
- `c/272/图片/03-full-unittest.png`
- `c/272/图片/04-source-encoding.png`
- `c/272/图片/05-docs-check.png`
- `c/272/解释/说明.md`

## 一句话总结

v272 让 promotion index 只把满足 clean batch-review requirement 的 promoted run 放入 compare inputs，避免不干净证据进入模型能力对比。
