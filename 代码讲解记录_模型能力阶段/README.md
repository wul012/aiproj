# MiniGPT 代码讲解记录_模型能力阶段

本目录从 v473 开始承接 MiniGPT 的模型能力、真实 tiny 训练对比、baseline/candidate 能力评估和后续能力提升讲解。前一阶段 `代码讲解记录_训练治理阶段/` 保留 v303-v472 的训练治理、promoted seed、receipt contract 和 CI 回归治理讲解。

## 写入规则

- 编号继续沿用全局序号，从 `487-v473-...` 开始。
- 旧的 `代码讲解记录_训练治理阶段/` 不迁移，只作为 v303-v472 历史阶段保留。
- 如果本目录以后也明显过密或主题再次分叉，再新建同级目录承接后续内容。
- 每篇讲解仍然按仓库规则写清目标、边界、关键文件、输入输出、测试覆盖、运行证据和一句话总结。

## 当前索引

487-v473-baseline-candidate-capability-delta.md
 -> v473 code explanation: carry real tiny training loss and generation-quality deltas into the baseline-candidate eval loop.

488-v474-model-capability-ladder.md
 -> v474 code explanation: run a same-seed tiny training scale ladder and report loss/score/flag trends.

489-v475-model-capability-ladder-stability.md
 -> v475 code explanation: replay the tiny ladder across seeds and summarize stability of loss/score/flag deltas.

490-v476-model-capability-stall-diagnostic.md
 -> v476 code explanation: compare first/last ladder prompt cases and explain why eval scores stayed flat.

491-v477-model-capability-token-budget-probe.md
 -> v477 code explanation: run longer-token tiny ladders and compare prompt-level stall deltas.

492-v478-model-capability-token-budget-stability.md
 -> v478 code explanation: replay the token-budget probe across seeds and separate stable budget relief from model-quality progress.

## 一句话总览

本目录把 MiniGPT 后续重心从“证明训练治理链路完整”转向“用真实 tiny 训练证据观察模型能力是否变化”。
