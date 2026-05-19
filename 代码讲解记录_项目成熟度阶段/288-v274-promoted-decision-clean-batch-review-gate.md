# v274 promoted decision clean batch review gate

## 本版目标和边界

v274 的目标是把 v273 promoted comparison 已经输出的 clean batch-review evidence 继续带到 promoted baseline decision。此前 comparison 层已经会把不满足 clean requirement 的 promoted row 排除出 compared runs，但 decision 层仍需要自己保留 selected clean 状态、汇总 clean/unclean 计数，并在 dirty clean-required row 仍存在于 promotions 证据里时明确拒绝它成为 baseline candidate。

本版不做新的训练、不改变模型结构、不改变 promoted comparison 的过滤规则，也不把 review 状态自动提升为 accepted。它只让 promoted baseline decision 消费上游 clean batch-review 契约，并把结果写进报告、CLI 和测试。

## 前置链路

v268 把 `require_clean_batch_review` 加到 standalone run decision。v269 接入 workflow。v270 接入 execution handoff。v271 接入 promotion acceptance。v272 接入 promotion index。v273 接入 promoted comparison。v274 是 baseline decision 层的防漏网：即使 dirty clean-required row 因兼容输入或旧报告出现在 decision 的 promotions 里，也不能被选成下一轮 promoted baseline。

## 关键文件

`src/minigpt/promoted_training_scale_decision.py`

该文件负责读取 `promoted_training_scale_comparison.json`，生成 baseline decision。v274 在 `_promotion_rows()` 中保留：

- `handoff_require_clean_batch_review`
- `handoff_clean_batch_review_status`

并在 `_rejection_reasons()` 中新增拒绝条件：

```python
if row.get("handoff_require_clean_batch_review") and row.get("handoff_clean_batch_review_status") != "clean":
    reasons.append("clean batch-review requirement is not clean")
```

这表示 dirty clean-required promoted row 可以留在 evidence 里，但不能进入 candidate selection。

`src/minigpt/promoted_training_scale_decision_review.py`

该文件是 decision 层的 handoff review summary helper。v274 新增 selected clean 状态和聚合计数：

- `selected_handoff_require_clean_batch_review`
- `selected_handoff_clean_batch_review_status`
- `handoff_require_clean_batch_review_count`
- `handoff_clean_batch_review_count`
- `handoff_unclean_batch_review_count`
- `comparison_ready_handoff_require_clean_batch_review_count`
- `comparison_ready_handoff_clean_batch_review_count`
- `comparison_ready_handoff_unclean_batch_review_count`

同时新增 `append_decision_handoff_clean_batch_recommendations()`。如果 selected baseline 本身不 clean，它会要求先修复 selected clean requirement；如果 dirty clean-required row 只存在于 rejected inputs，它会提示这些输入应继续被排除在 baseline selection 外。

`src/minigpt/promoted_training_scale_decision_artifacts.py`

该文件负责 decision JSON/CSV/Markdown/HTML 输出。v274 把 clean batch-review 字段加入 CSV 字段、Markdown 摘要和 HTML stats 卡片，让人工审查和自动化读取都能看到：

- selected baseline 是否要求 clean batch-review；
- selected baseline 的 clean 状态；
- 所有 handoff 中 clean-required、clean、unclean 的数量；
- comparison-ready 输入中的 clean-required、clean、unclean 数量。

这些产物是最终 decision 证据，可被后续 promoted seed 或归档模块消费。

`scripts/decide_promoted_training_scale_baseline.py`

该 CLI 现在打印 clean batch-review 字段。这样 CI、日志截图和脚本调用方不用打开 JSON，也能看到 selected clean 状态和 ready clean 计数。

`tests/test_promoted_training_scale_decision.py`

测试新增 clean batch-review 场景：

- `alpha` 和 `beta` 都是 clean-required 且 clean；
- `dirty` 是 clean-required 但 status 为 review；
- `dirty` 仍保留在 promotions 证据里，但被 decision 以 `clean batch-review requirement is not clean` 拒绝；
- selected baseline 仍是 `beta`，decision 状态为 review，因为 rejected evidence 需要人工审查；
- CSV、Markdown、HTML 和 CLI stdout 都能看到 clean batch-review 字段。

## 输入输出

输入是 promoted comparison 产物：

```json
{
  "promotions": [
    {
      "name": "dirty",
      "promotion_status": "promoted",
      "promoted_for_comparison": false,
      "handoff_require_clean_batch_review": true,
      "handoff_clean_batch_review_status": "review"
    }
  ]
}
```

输出时该 row 会进入 rejected runs：

```json
{
  "name": "dirty",
  "reasons": [
    "run was not promoted for comparison",
    "clean batch-review requirement is not clean"
  ]
}
```

这让 decision 报告能解释：它不是丢失了一条 promoted evidence，而是有意拒绝把不干净 evidence 作为 baseline。

## 运行证据

本版运行截图和解释归档在 `c/274`：

- focused promoted decision tests；
- promotion/promotion-index/promoted-comparison/promoted-decision 相关链路测试；
- 全量 unittest；
- source encoding hygiene；
- Playwright 渲染的 promoted decision HTML；
- 文档和字段引用检查。

## 一句话总结

v274 让 promoted baseline decision 自己消费 clean batch-review 证据，避免 dirty clean-required promoted row 被误选为下一轮训练 baseline。
