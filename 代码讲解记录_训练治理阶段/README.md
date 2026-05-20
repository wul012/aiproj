# MiniGPT 代码讲解记录_训练治理阶段

本目录从 v303 开始承接 MiniGPT 的训练治理、文档分流和后续训练链路讲解。前一阶段 `代码讲解记录_项目成熟度阶段/` 已经覆盖 v48-v302，内容包括 maturity summary、benchmark scorecard、本地推理、training portfolio、training scale、promoted seed handoff、CI assurance 和 batch CI regression review。

## 写入规则

- 编号继续沿用全局序号，从 `317-v303-...` 开始。
- 旧的 `代码讲解记录_项目成熟度阶段/` 不迁移，只作为 v48-v302 历史阶段保留。
- 如果本目录以后也明显过密或主题再次分叉，再新建同级目录承接后续内容。
- 每篇讲解仍然按仓库规则写清目标、边界、关键文件、输入输出、测试覆盖、运行证据和一句话总结。

## 当前索引

317-v303-training-governance-doc-stage-split.md
 -> v303 code explanation: close the dense v48-v302 project-maturity explanation directory as history and start the same-level training-governance documentation stage.

318-v304-training-scale-run-ci-regression-carryover.md
 -> v304 code explanation: carry batch CI regression review context into gated training-scale run reports and training-scale run comparisons.

319-v305-training-scale-decision-ci-regression-gate.md
 -> v305 code explanation: carry batch CI regression context into training-scale run decisions and clean batch-review execution gating.

320-v306-training-scale-workflow-handoff-ci-regression-carryover.md
 -> v306 code explanation: carry decision-level batch CI regression evidence into the consolidated workflow and execution handoff guard.

321-v307-training-scale-promotion-ci-regression-carryover.md
 -> v307 code explanation: carry handoff batch CI regression evidence into promotion reports and strict clean-batch promotion acceptance.

322-v308-training-scale-promotion-index-ci-regression-filtering.md
 -> v308 code explanation: carry promotion handoff CI regression evidence into promotion index rows, summaries, outputs, and compare-input filtering.

## 一句话总览

本目录让 MiniGPT 的文档治理从“继续向一个成熟度目录堆版本”转为“阶段化同级承接”，后续训练治理文档可以继续增长而不压垮旧阶段索引。
