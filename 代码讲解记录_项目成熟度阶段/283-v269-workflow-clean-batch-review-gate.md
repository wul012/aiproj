# v269 workflow clean batch review gate

## 本版目标和边界

v269 的目标是把 v268 的 clean batch-review gate 从 standalone run decision 继续接入 consolidated training-scale workflow。此前 `build_training_scale_run_decision()` 已经可以在 `require_clean_batch_review=True` 时拒绝 batch review actions、blocker actions 和 maturity coverage regressions，但一键 workflow 仍然只能直接消费默认 decision 语义。本版让 workflow API、CLI、summary 和 artifact 都能显式表达这个 gate。

本版不改变：

- 默认 workflow 行为；
- gate profile、comparison scoring 和 run selection 排序；
- `--decision-require-suite-consistency` 的 suite guard 语义；
- nested `plan/`、`runs/<profile>/`、`comparison/`、`decision/` artifact 结构；
- execute command 仍然只是 reviewed handoff，不自动执行训练。

## 前置链路

v253-v261 已经把 batch comparison review/blocker context 从 gated runs 带到 comparison、decision、handoff、promotion、promotion index、promoted comparison、promoted decision、promoted seed 和 seed handoff。v268 在 standalone run decision 层新增了 `require_clean_batch_review`。v269 继续补齐入口层：如果团队使用 `scripts/run_training_scale_workflow.py` 作为“一条命令跑完整训练规模治理链路”的入口，也能启用同一套 clean batch-review 自动化阻断规则。

## 关键文件

### `src/minigpt/training_scale_workflow.py`

`run_training_scale_workflow()` 新增参数：

```python
decision_require_clean_batch_review: bool = False
```

这个参数会传给 `build_training_scale_run_decision(require_clean_batch_review=...)`。workflow report 顶层新增：

- `decision_require_clean_batch_review`
- `require_clean_batch_review`

workflow summary 新增：

- `decision_require_clean_batch_review`
- `clean_batch_review_status`

当 strict gate 被启用并且 status 不是 `clean` 时，workflow recommendations 会提醒先处理 batch review、blocker 和 coverage-regression evidence，再把该结果当作 clean execute automation 使用。

### `scripts/run_training_scale_workflow.py`

新增 CLI 参数：

```powershell
--decision-require-clean-batch-review
```

脚本输出新增：

```text
clean_batch_review_status=<clean|review|blocker>
```

这让命令行 smoke、CI 日志和人工复核都能直接看到 workflow 的 clean batch-review 状态，而不用先打开 JSON。

### `src/minigpt/training_scale_workflow_artifacts.py`

workflow CSV、Markdown、HTML 都新增展示：

- `decision_require_clean_batch_review`
- `clean_batch_review_status`

这个文件负责把机器字段投影成人能读的证据。v269 的重点不是只在 JSON 里放字段，而是让 artifact 读者也能理解 workflow 是否启用了 strict clean batch-review gate，以及当前 comparison 为什么被拦截。

### `tests/test_training_scale_workflow.py`

新增两类测试：

- 同一份 fixture 下，默认 workflow 仍然得到 `decision_status=review`，而启用 `decision_require_clean_batch_review=True` 后变成 `blocked`；
- CSV/Markdown/HTML 都渲染 clean batch-review 字段，避免 workflow JSON 与人工报告脱节。

## 输入输出

输入仍然是源数据路径、profile 列表、baseline profile 和 out-root。新增控制项：

- Python: `decision_require_clean_batch_review=True`
- CLI: `--decision-require-clean-batch-review`

输出 report 新增字段示例：

```json
{
  "decision_require_clean_batch_review": true,
  "require_clean_batch_review": true,
  "summary": {
    "decision_require_clean_batch_review": true,
    "clean_batch_review_status": "review",
    "decision_status": "blocked"
  }
}
```

nested decision artifact 仍然由 run decision 模块写出，因此 workflow 与 standalone decision 使用同一套 status domain 和 rejection 规则。

## 测试覆盖

- 聚焦测试覆盖 workflow 默认行为、strict clean batch-review 阻断、nested decision artifact 字段和 artifact 渲染字段。
- CLI smoke 覆盖 `--decision-require-clean-batch-review` 从命令行进入 workflow，并确认 strict workflow 在 review evidence 下返回非零退出。
- 全量 unittest 保护 training-scale、report-utils、governance 和 UI 周边模块不受影响。
- source encoding hygiene 检查确认新增脚本、代码、文档没有 BOM 或语法问题。

## 证据归档

运行截图和解释归档在 `c/269`：

- `c/269/图片/01-focused-tests.png`
- `c/269/图片/02-workflow-clean-batch-gate-smoke.png`
- `c/269/图片/03-full-unittest.png`
- `c/269/图片/04-source-encoding.png`
- `c/269/图片/05-docs-check.png`
- `c/269/解释/说明.md`

## 一句话总结

v269 把 clean batch-review gate 从 standalone decision 补齐到一键 workflow 入口，让训练规模治理链路可以在同一条命令里拒绝 review/blocker/coverage-regression execute evidence。
