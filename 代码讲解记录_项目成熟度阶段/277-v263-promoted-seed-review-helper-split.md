# v263 promoted seed review helper split

## 本版目标和边界

v263 的目标是继续执行“传播完成后的结构收口”。v260 已经把 promoted baseline decision 的 handoff batch review context 传入 promoted next-cycle seed；v262 又把 seed handoff 的 review helper 拆到独立模块。回头看 promoted seed 本身，`src/minigpt/promoted_training_scale_seed.py` 仍有 586 行，里面同时承担 orchestration、suite guard 映射、handoff batch-review 映射、summary projection 和 recommendation 追加。本版把后四类 helper 逻辑抽到 `promoted_training_scale_seed_review.py`。

本版不改变：

- promoted seed 的 `seed_status` 判定；
- next plan command 生成；
- `promoted_training_scale_seed.json/csv/md/html` 字段；
- CLI 输出；
- v260 建立的 selected handoff batch review/blocker context。

## 前置链路

v250-v263 的主线是：coverage/maturity review signal 进入 portfolio comparison 后，逐层进入 batch、scale run、decision、handoff、promotion、promotion index、promoted comparison、promoted decision、promoted seed 和 seed handoff。v263 不新增传播层，而是在 promoted seed 层收口已有逻辑，避免“证据链越完整，单文件越重”。

## 关键文件

### `src/minigpt/promoted_training_scale_seed_review.py`

这是本版新增 helper 模块，主要函数包括：

- `build_seed_handoff_suite_guard()`：从 promoted decision summary 和 selected baseline fallback 中提取 handoff suite guard context。
- `build_seed_handoff_batch_review()`：从 decision summary 和 selected baseline fallback 中提取 selected handoff batch review/blocker context，并统一 blocker reason list。
- `build_seed_handoff_batch_review_summary()`：把 `baseline_seed.handoff_batch_review` 投影成 summary 字段，供 artifacts 和 CLI 使用。
- `append_seed_handoff_batch_review_recommendation()`：根据 selected batch review status 追加 review/blocker recommendation。

这些逻辑之前散落在 `promoted_training_scale_seed.py` 中，本版后集中到 helper 文件。

### `src/minigpt/promoted_training_scale_seed.py`

主文件现在更接近 orchestration：读取 promoted decision、解析 selected baseline、读取 selected run、准备 source rows、计算 blockers、生成 next plan command、组合 seed report。它通过 helper 生成：

- `baseline_seed.handoff_suite_guard`
- `baseline_seed.handoff_batch_review`
- summary 中的 batch-review 字段
- recommendations 中的 batch-review 提醒

拆分后主文件从 586 行降到 454 行，新 helper 是 159 行。

### `tests/test_promoted_training_scale_seed_review.py`

新增 helper 级测试覆盖：

- summary 优先、selected fallback 次之的 batch-review 映射；
- suite guard 从 summary/selected 两侧组合；
- summary projection 和 recommendation 复用同一个 seed shape。

### `tests/test_promoted_training_scale_seed.py`

原 promoted seed 主流程测试继续通过，说明 JSON/CSV/Markdown/HTML、CLI 和 recommendation 语义没有被拆分破坏。

## 输入输出

输入仍然是 promoted baseline decision JSON 或目录，以及 next-cycle plan sources。输出仍然是：

- `promoted_training_scale_seed.json`
- `promoted_training_scale_seed.csv`
- `promoted_training_scale_seed.md`
- `promoted_training_scale_seed.html`

本版没有新增字段，只改变内部 helper 边界。

## 测试覆盖

- 聚焦测试运行 `tests.test_promoted_training_scale_seed_review` 和 `tests.test_promoted_training_scale_seed`。
- contract smoke 构建带 handoff batch review context 的 seed report，检查 `seed_status=ready`、`selected_handoff_selected_batch_review_status=blocker`、blocker action count、recommendation 和文件行数。
- 全量 unittest 确认其他治理链路未受影响。
- source encoding 检查确认新文件没有 BOM、不可打印字符或语法错误。

## 证据归档

运行截图和解释归档在 `c/263`：

- `c/263/图片/01-focused-tests.png`
- `c/263/图片/02-contract-smoke.png`
- `c/263/图片/03-full-unittest.png`
- `c/263/图片/04-source-encoding.png`
- `c/263/图片/05-docs-check.png`
- `c/263/解释/说明.md`

## 一句话总结

v263 把 promoted next-cycle seed 的 suite guard 和 handoff batch-review 映射逻辑抽成独立 helper，让主流程从 586 行降到 454 行，同时保持 promoted seed 的输出契约不变。
