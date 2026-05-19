# v275 promoted seed clean batch review gate

## 本版目标和边界

v275 的目标是把 v274 promoted baseline decision 已经输出的 clean batch-review evidence 继续带到 promoted next-cycle seed。此前 seed 层已经能继承 selected suite guard 和 selected handoff batch review；本版补齐 selected clean batch-review requirement/status 以及 clean/unclean 聚合计数，让下一轮训练计划种子不会丢失 baseline 是否干净的上下文。

本版不执行真实训练、不改变 planning command 的参数语义，也不改变 decision 的 accepted/review 状态判断。它只负责在 seed artifact 中保留和呈现 clean batch-review evidence。

## 前置链路

v268 把 clean batch-review gate 加到 standalone run decision。v269 接入 workflow。v270 接入 execution handoff。v271 接入 promotion acceptance。v272 接入 promotion index。v273 接入 promoted comparison。v274 接入 promoted baseline decision。v275 是 next-cycle seed 层的延续：选中的 baseline 进入下一轮训练计划之前，seed artifact 必须知道它是否来自 clean batch-review。

## 关键文件

`src/minigpt/promoted_training_scale_seed_review.py`

该文件新增 clean batch-review helper：

- `build_seed_handoff_clean_batch_review()`
- `build_seed_handoff_clean_batch_review_summary()`
- `append_seed_handoff_clean_batch_recommendation()`

输入来自 decision summary 和 selected baseline。字段包括：

- `selected_handoff_require_clean_batch_review`
- `selected_handoff_clean_batch_review_status`
- `handoff_require_clean_batch_review_count`
- `handoff_clean_batch_review_count`
- `handoff_unclean_batch_review_count`
- `comparison_ready_handoff_require_clean_batch_review_count`
- `comparison_ready_handoff_clean_batch_review_count`
- `comparison_ready_handoff_unclean_batch_review_count`

`src/minigpt/promoted_training_scale_seed.py`

seed builder 新增 `handoff_clean_batch_review` 区块，并把 clean summary 合并进 seed summary。recommendations 也会调用 clean helper：如果 selected clean status 不干净，提示先修复；如果 dirty clean-required 只存在于 rejected decision inputs，提示这些 input 不应进入 next-cycle seed baseline。

`src/minigpt/promoted_training_scale_seed_artifacts.py`

该文件负责 seed JSON/CSV/Markdown/HTML 输出。v275 把 clean fields 加入 CSV 字段、Markdown 摘要、HTML stats 和 baseline section。这样 seed 报告既能给人读，也能被后续 seed handoff 或归档脚本读取。

`scripts/build_promoted_training_scale_seed.py`

CLI 输出新增 selected clean status 和 clean counts。这样命令日志截图能直接证明 seed 是否继承了 promoted decision 的 clean evidence。

`tests/test_promoted_training_scale_seed.py`

测试新增 clean batch-review 场景：

- decision selected baseline 是 clean-required 且 clean；
- decision summary 中仍保留一个 rejected dirty clean-required 输入；
- seed summary、CSV、Markdown、HTML、CLI stdout 都保留 selected clean status 和 clean counts；
- recommendations 提醒 rejected dirty clean-required decision inputs 应继续排除在 next-cycle seed baseline 外。

## 输入输出

输入 decision summary 示例：

```json
{
  "selected_handoff_require_clean_batch_review": true,
  "selected_handoff_clean_batch_review_status": "clean",
  "handoff_unclean_batch_review_count": 1
}
```

seed 输出新增：

```json
{
  "handoff_clean_batch_review": {
    "selected_handoff_require_clean_batch_review": true,
    "selected_handoff_clean_batch_review_status": "clean",
    "handoff_unclean_batch_review_count": 1
  }
}
```

这让下一轮计划种子可以解释：baseline 是 clean 的，但上游 rejected evidence 中仍有 dirty clean-required 输入需要保留审计痕迹。

## 运行证据

本版运行截图和解释归档在 `c/275`：

- promoted seed focused tests；
- promoted comparison/decision/seed/seed handoff 相关链路测试；
- 全量 unittest；
- source encoding hygiene；
- Playwright 渲染的 promoted seed HTML；
- 文档和字段引用检查。

## 一句话总结

v275 让 promoted next-cycle seed 继承 clean batch-review 证据，避免下一轮训练计划丢失 baseline 是否干净的判断依据。
