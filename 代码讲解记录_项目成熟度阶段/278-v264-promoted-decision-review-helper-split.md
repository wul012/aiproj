# v264 promoted decision review helper split

## 本版目标和边界

v264 的目标是继续做 contract-preserving refactor。`src/minigpt/promoted_training_scale_decision.py` 是当前最大 Python 文件，达到 716 行，其中既有 promoted baseline 选择逻辑，也有 selected handoff suite/batch-review summary projection、recommendation 和 artifacts 渲染。本版只拆 selected handoff review 相关 helper，不碰 baseline selection 和 artifact rendering。

本版不改变：

- promoted baseline 的选择规则；
- `decision_status` 判定；
- `promoted_training_scale_decision.json/csv/md/html` 字段；
- CLI 输出；
- v259-v263 建立的 handoff batch-review 可见性。

## 前置链路

v259 让 promoted decision 保存 selected handoff batch-review context，v260-v261 继续把它传到 promoted seed 和 seed handoff。v262-v263 先把下游两个模块的 review helper 拆出。v264 回到 promoted decision 层，把最早的 selected handoff review projection 也拆出，形成同链路的三段 helper：

- `promoted_training_scale_decision_review.py`
- `promoted_training_scale_seed_review.py`
- `promoted_training_scale_seed_handoff_review.py`

## 关键文件

### `src/minigpt/promoted_training_scale_decision_review.py`

这是本版新增 helper 模块，主要函数包括：

- `build_decision_handoff_review_summary()`：从 comparison summary、promotions 和 selected baseline 中生成 selected handoff suite/batch-review summary 字段。
- `append_decision_handoff_batch_recommendations()`：根据 selected status 优先追加 blocker/review recommendation；如果 selected 本身干净但其他 comparison-ready promoted input 有 blocker，也保留 review context。

模块内部保留 `_summary_number()` 和 `_int()`，只服务本模块的 fallback 计算。

### `src/minigpt/promoted_training_scale_decision.py`

主文件继续负责：

- 读取 promoted comparison；
- 收集 promotion rows；
- 应用 rejection rules；
- 选择 selected baseline；
- 生成 artifacts。

`_summary()` 现在先生成核心 decision 字段，再通过 `build_decision_handoff_review_summary()` 合并 handoff review 字段。`_recommendations()` 通过 `append_decision_handoff_batch_recommendations()` 追加 handoff batch review 提醒。

拆分后主文件从 716 行降到 600 行，新 helper 是 157 行。主文件仍偏大，因为 CSV/Markdown/HTML 渲染仍在同一文件里。

### `tests/test_promoted_training_scale_decision_review.py`

新增 helper 级测试覆盖：

- selected handoff suite 和 batch-review context 可以被正确投影到 summary；
- comparison summary 缺少 totals 时，可以从 promoted rows 推导 review/blocker counts、action totals 和 blocker reasons；
- recommendation 优先 selected status，其次才提示其他 comparison-ready blockers。

### `tests/test_promoted_training_scale_decision.py`

原 promoted decision 主流程测试继续通过，说明 JSON/CSV/Markdown/HTML、CLI 和 recommendations 没有被 helper 拆分破坏。

## 输入输出

输入仍然是 promoted comparison JSON 或目录。输出仍然是：

- `promoted_training_scale_decision.json`
- `promoted_training_scale_decision.csv`
- `promoted_training_scale_decision.md`
- `promoted_training_scale_decision.html`

本版没有新增字段，只改变内部 helper 边界。

## 测试覆盖

- 聚焦测试运行 `tests.test_promoted_training_scale_decision_review` 和 `tests.test_promoted_training_scale_decision`。
- contract smoke 构建带 handoff batch review context 的 decision report，检查 `decision_status=review`、selected batch review、derived totals、recommendation 和文件行数。
- 全量 unittest 确认其他治理链路未受影响。
- source encoding 检查确认新文件没有 BOM、不可打印字符或语法错误。

## 证据归档

运行截图和解释归档在 `c/264`：

- `c/264/图片/01-focused-tests.png`
- `c/264/图片/02-contract-smoke.png`
- `c/264/图片/03-full-unittest.png`
- `c/264/图片/04-source-encoding.png`
- `c/264/图片/05-docs-check.png`
- `c/264/解释/说明.md`

## 一句话总结

v264 把 promoted baseline decision 的 selected handoff suite/batch-review summary 和 recommendation helper 抽成独立模块，让主文件从 716 行降到 600 行，同时保持 promoted decision 输出契约不变。
