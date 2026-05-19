# v271 promotion clean batch review gate

## 本版目标和边界

v271 的目标是把 handoff clean batch-review requirement 继续带到 training-scale promotion acceptance。此前 v270 已经能在执行前 handoff 边界阻断不满足 clean batch-review requirement 的 workflow，但 promotion acceptance 仍主要消费 handoff status 和 selected batch review status。本版让 promotion 明确读取 handoff 的 clean batch-review guard，并在 requirement 未满足时阻断 promotion。

本版不改变：

- clean handoff 的 promotion 成功路径；
- variant artifact 检查规则；
- suite guard 的已有字段和推荐语义；
- promoted comparison、promotion index、promoted seed 的输入结构；
- handoff 的执行逻辑。

## 前置链路

v268 在 run decision 层加入 `require_clean_batch_review`。v269 将该 gate 接入 consolidated workflow。v270 将 workflow requirement 带到 execution handoff。v271 继续推进到 promotion acceptance，避免一个被 handoff 标记为不满足 clean requirement 的结果在 promotion 阶段被误判成可接受基线。

## 关键文件

### `src/minigpt/training_scale_promotion.py`

新增 `_clean_batch_review_guard()`，从 handoff 顶层 `clean_batch_review_guard` 和 `summary` 中读取：

- `handoff_require_clean_batch_review`
- `handoff_clean_batch_review_status`
- batch comparison review/blocker/regression 计数
- blocker reasons

`_issues()` 新增 blocker：

```text
handoff requires clean batch-review evidence but status is not clean
```

summary 新增：

- `handoff_require_clean_batch_review`
- `handoff_clean_batch_review_status`

recommendations 在 requirement 未满足时优先提示先解决 handoff clean batch-review requirement，再接受 promotion evidence。

### `src/minigpt/training_scale_promotion_artifacts.py`

promotion CSV、Markdown、HTML 都新增展示 handoff clean batch-review requirement 和 status。这样 promotion 报告本身就能解释为什么被阻断，而不需要读者回跳到 handoff JSON。

### `scripts/build_training_scale_promotion.py`

CLI 输出新增：

```text
handoff_clean_batch_review_status=<clean|review|blocker>
```

当 promotion 因 clean batch-review requirement 被阻断时，脚本仍然返回非零状态，便于 CI 或自动化使用。

### `tests/test_training_scale_promotion.py`

新增覆盖：

- clean requirement 且 status=`clean` 时 promotion 仍然 `promoted`；
- requirement 未满足时 promotion `blocked`，CLI 返回 1；
- CSV/Markdown/HTML 和 CLI stdout 都展示 handoff clean batch-review 字段。

## 输入输出

输入是 `training_scale_handoff.json` 或 handoff 目录。新增消费字段：

```json
{
  "clean_batch_review_guard": {
    "decision_require_clean_batch_review": true,
    "clean_batch_review_status": "review"
  }
}
```

输出 promotion report 新增：

```json
{
  "clean_batch_review_guard": {
    "handoff_require_clean_batch_review": true,
    "handoff_clean_batch_review_status": "review"
  },
  "summary": {
    "promotion_status": "blocked",
    "handoff_require_clean_batch_review": true,
    "handoff_clean_batch_review_status": "review"
  }
}
```

## 测试覆盖

- promotion 聚焦测试覆盖 clean guard 汇总、promoted 兼容路径、blocked 路径、artifact 渲染和 CLI 输出。
- 全量 unittest 保护训练规模链路、报告工具、UI、发布治理和数据治理模块。
- source encoding hygiene 检查保证新增代码和文档没有 BOM 或语法错误。

## 证据归档

运行截图和解释归档在 `c/271`：

- `c/271/图片/01-focused-tests.png`
- `c/271/图片/02-promotion-clean-batch-gate-smoke.png`
- `c/271/图片/03-full-unittest.png`
- `c/271/图片/04-source-encoding.png`
- `c/271/图片/05-docs-check.png`
- `c/271/解释/说明.md`

## 一句话总结

v271 把 clean batch-review requirement 推到 promotion acceptance，确保未满足 clean handoff gate 的训练结果不能被误提升为 promotion-ready evidence。
