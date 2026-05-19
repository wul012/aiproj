# v262 promoted seed handoff review helper split

## 本版目标和边界

v262 的目标是收束 v261 带来的文件压力。v261 把 promoted seed handoff batch review context 接入 seed handoff 报告层后，`src/minigpt/promoted_training_scale_seed_handoff.py` 达到 601 行，已经超过 aiproj 当前约 500 行的局部压力阈值。本版把 seed handoff 的 review helper、suite alignment、clean-evidence readiness、clean-evidence requirement、batch-review summary 和 review recommendations 拆到独立模块。

本版不改变：

- seed handoff 的状态判定规则；
- `promoted_training_scale_seed_handoff.json/csv/md/html` 的字段契约；
- CLI 输出字段；
- clean-evidence status domain；
- v261 batch review/blocker context 的传播语义。

## 前置链路

v250-v261 连续把 coverage/maturity review signal 从 portfolio comparison 向 batch、scale run、decision、handoff、promotion、promotion index、promoted comparison、promoted decision、promoted seed 和 seed handoff 传播。v262 没有继续扩展传播层，而是对最后一层 seed handoff 做一次局部收口，避免“字段传播完成后把编排文件留成大文件”。

## 关键文件

### `src/minigpt/promoted_training_scale_seed_handoff_review.py`

这是本版新增的 helper 模块，负责 seed handoff 的证据判定小逻辑：

- `SeedHandoffCleanEvidenceStatus` 和 `SeedHandoffCleanEvidenceRequirementStatus`：保留原 clean-evidence 状态域。
- `SeedHandoffCleanEvidenceReadiness` 和 `SeedHandoffCleanEvidenceRequirement`：保留原 TypedDict 契约。
- `build_seed_handoff_batch_review_summary()`：从 `baseline_seed.handoff_batch_review` 提取 selected batch review/blocker 字段和 comparison-ready 汇总字段，并把 reason list 归一成字符串列表。
- `build_seed_handoff_suite_alignment()`：判断 selected handoff、seed 和 plan suite path 的一致性，输出 `consistent/pending-plan/missing/mismatch`。
- `build_seed_handoff_clean_evidence_readiness()`：把 handoff 状态和 suite alignment 映射为 clean-evidence readiness。
- `build_seed_handoff_clean_evidence_requirement()`：保留原 reusable library contract，用于 `--require-clean-evidence` 和测试调用。
- `build_seed_handoff_review_recommendations()`：统一拼装 suite alignment、clean-evidence requirement、batch review 三类 review 建议。

### `src/minigpt/promoted_training_scale_seed_handoff.py`

主文件现在回到 orchestration：加载 seed、运行或计划 command、读取 plan report、收集 artifacts、构造 summary、写 recommendations。它从 helper 模块 import 并 re-export 原有 public contract，因此旧测试仍然可以从 `minigpt.promoted_training_scale_seed_handoff` 导入 clean-evidence 类型和 builder。

拆分后文件行数从 601 降到 377，新 helper 是 268 行，职责边界更清楚。

### `tests/test_promoted_training_scale_seed_handoff_review.py`

新增 helper 级测试，直接覆盖三类低层逻辑：

- batch review summary 会保留 selected status、review/blocker action count，并把 blocker reasons 归一成字符串列表；
- suite alignment 在没有 generated plan 时输出 `pending-plan`，不误报 mismatch；
- review recommendations 会同时包含 pending-plan、clean-evidence requirement fail 和 selected batch blocker 提醒。

### `tests/test_promoted_training_scale_seed_handoff.py`

原有主流程测试继续通过，说明新 helper 没有破坏 v261 的 handoff summary、artifacts、CLI 和 recommendation 契约。

## 输入输出

输入仍然是 promoted seed JSON 或 promoted seed 目录。输出仍然是：

- `promoted_training_scale_seed_handoff.json`
- `promoted_training_scale_seed_handoff.csv`
- `promoted_training_scale_seed_handoff.md`
- `promoted_training_scale_seed_handoff.html`

本版没有新增报告字段，只改变内部实现位置。

## 测试覆盖

本版验证重点不是模型质量，而是契约保持：

- 聚焦测试运行 seed handoff helper 和原 seed handoff 测试；
- contract smoke 构建带 batch-review context 的 handoff report，检查 `handoff_status=planned`、`selected_handoff_selected_batch_review_status=blocker`、`seed_handoff_clean_evidence_status=pending-plan` 和 blocker recommendation；
- 全量 unittest 确认其他治理链路没有被 helper 拆分影响；
- source encoding 检查确认新文件没有 BOM、不可打印字符或语法错误。

## 证据归档

运行截图和解释归档在 `c/262`：

- `c/262/图片/01-focused-tests.png`
- `c/262/图片/02-contract-smoke.png`
- `c/262/图片/03-full-unittest.png`
- `c/262/图片/04-source-encoding.png`
- `c/262/图片/05-docs-check.png`
- `c/262/解释/说明.md`

## 一句话总结

v262 把 promoted seed handoff 的 review/clean-evidence/batch-review 判定逻辑抽成独立模块，让 seed handoff 主流程从 601 行降到 377 行，同时保持 v261 的输出契约不变。
