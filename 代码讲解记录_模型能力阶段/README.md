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

493-v479-model-capability-rubric-signal-audit.md
 -> v479 code explanation: audit remaining cap-12 rubric signals and identify required-term/data coverage blockers.

494-v480-model-capability-required-term-coverage.md
 -> v480 code explanation: trace required-term failures back to archived suite/corpus coverage and separate data absence from present-but-not-generated behavior.

495-v481-model-capability-required-term-uptake.md
 -> v481 code explanation: trace covered required terms into archived tiny generated/continuation text and show they were never generated.

496-v482-model-capability-required-term-scaffold-probe.md
 -> v482 code explanation: run real short required-term scaffold generations against archived tiny checkpoints and confirm no continuation uptake.

497-v483-model-capability-required-term-micro-training.md
 -> v483 code explanation: train a tiny scaffold-to-term checkpoint and observe targeted required-term continuation uptake.

498-v484-model-capability-required-term-holdout.md
 -> v484 code explanation: split required terms into train/holdout slices and show v483's targeted signal does not yet reproduce under the stricter split.

499-v485-model-capability-required-term-split-scan.md
 -> v485 code explanation: scan multiple required-term splits and find train-slice uptake without held-out generalization.

500-v486-model-capability-required-term-split-seed-stability.md
 -> v486 code explanation: repeat the best required-term split across seeds and show train-slice uptake is only partial.

501-v487-model-capability-required-term-balanced-corpus.md
 -> v487 code explanation: build a balanced required-term corpus candidate from v486 evidence before the next tiny-training rerun.

502-v488-model-capability-required-term-balanced-training.md
 -> v488 code explanation: train from the balanced corpus and diagnose missing prompt-leading alignment when continuation uptake stays zero.

503-v489-model-capability-required-term-prompt-leading-corpus.md
 -> v489 code explanation: rebuild the balanced corpus with prompt-leading rows so the next tiny training run matches probe prefix shape.

504-v490-model-capability-required-term-prompt-leading-training.md
 -> v490 code explanation: train from the prompt-leading corpus and show prefix alignment alone still does not produce required-term continuation uptake.

505-v491-model-capability-required-term-direct-prompt-training.md
 -> v491 code explanation: remove metadata and extra variants, then show direct prompt-to-term training still does not produce target-specific continuation uptake.

506-v492-model-capability-required-term-one-term-isolation.md
 -> v492 code explanation: train one checkpoint per required term and show single-target capacity appears before multi-term prompt-conditioned training works.

507-v493-model-capability-required-term-one-term-seed-stability.md
 -> v493 code explanation: repeat v492 successful one-term cases across seeds and identify stable single-target capacity signals.

508-v494-model-capability-required-term-pair-curriculum.md
 -> v494 code explanation: train two stable one-term targets per checkpoint and expose the current pair-level interference boundary.

509-v495-model-capability-required-term-pair-rebalance.md
 -> v495 code explanation: rebalance v494 partial two-term curricula and observe the first full-hit pair-capacity signal.

510-v496-model-capability-required-term-pair-rebalance-seed-stability.md
 -> v496 code explanation: repeat the v495 full-hit pair across seeds and show the signal is not yet stable.

511-v497-model-capability-required-term-pair-capacity-sweep.md
 -> v497 code explanation: sweep training budget, embedding width, and corpus density for the fragile v496 pair before expanding target groups.

512-v498-model-capability-required-term-pair-decoding-sweep.md
 -> v498 code explanation: reuse v497 partial checkpoints and sweep decoding profiles before changing corpus or model capacity again.

513-v499-model-capability-required-term-pair-prompt-separation-audit.md
 -> v499 code explanation: audit v497 pair-capacity corpora after v498 decoding failed and identify prompt-target leakage in contrast rows.

514-v500-model-capability-required-term-pair-contrast-free-training.md
 -> v500 code explanation: train real contrast-free fixed/loss pair checkpoints after the v499 audit and report the remaining partial-only boundary.

515-v501-model-capability-required-term-pair-loss-branch-sweep.md
 -> v501 code explanation: train clean rescue variants for the missed loss branch and show the resulting fixed/loss tradeoff.

516-v502-model-capability-required-term-pair-branch-retention-sweep.md
 -> v502 code explanation: train balanced clean variants after the v501 tradeoff and show branch retention is still not solved.

517-v503-model-capability-required-term-pair-forced-choice-diagnostic.md
 -> v503 code explanation: score v502 checkpoints with teacher-forced fixed/loss choices and separate internal preference from free-generation collapse.

518-v504-model-capability-required-term-pair-generation-gap.md
 -> v504 code explanation: compare v503 forced-choice winners with v502 free-generation probes and classify internal-only generation gaps.

519-v505-model-capability-required-term-pair-decoding-gap-probe.md
 -> v505 code explanation: probe the v504 best gap checkpoint with small decoding profiles and show partial expression without full pair recovery.

520-v506-model-capability-required-term-pair-decoding-path-trace.md
 -> v506 code explanation: replay v505 decoding probes and show late expression after first-token sampling misses.

521-v507-model-capability-required-term-pair-first-token-repair.md
 -> v507 code explanation: force expected first tokens after v506 and show constrained repair improves partial expression but not full pair recovery.

522-v508-model-capability-required-term-pair-prefix-completion-sweep.md
 -> v508 code explanation: sweep forced required-term prefix lengths and show fixed needs a longer forced span than loss.

523-v509-model-capability-required-term-pair-diagnostic-rollup.md
 -> v509 code explanation: roll up v503-v508 diagnostics and choose continuation-span objective as the next experiment.

524-v510-model-capability-required-term-pair-continuation-span-objective.md
 -> v510 code explanation: train a fixed/loss continuation-span candidate and compare source vs candidate prefix boundaries.

525-v511-model-capability-required-term-pair-continuation-span-stability.md
 -> v511 code explanation: repeat the continuation-span objective across seeds and confirm stable prefix gain without full generation recovery.

526-v512-model-capability-required-term-pair-continuation-span-heldout.md
 -> v512 code explanation: probe source and held-out alias prompts against v511 seed checkpoints and record fixed-only alias signal.

527-v513-model-capability-required-term-pair-continuation-span-alias-matrix.md
 -> v513 code explanation: expand held-out aliases into a matrix and show fixed-only coverage while loss remains missing.

528-v514-model-capability-required-term-pair-loss-alias-objective.md
 -> v514 code explanation: train a tiny loss-alias objective from v513's missing loss prompts and recover all loss aliases in one seed.

529-v515-model-capability-required-term-pair-loss-alias-stability.md
 -> v515 code explanation: repeat the loss-alias objective across seeds and classify the recovery as stable partial rather than stable full.

530-v516-model-capability-required-term-pair-loss-alias-focus.md
 -> v516 code explanation: boost v515 missed loss-alias rows and show row density alone does not repair seed-515 misses.

531-v517-model-capability-required-term-pair-loss-alias-normalized-audit.md
 -> v517 code explanation: audit v516 strict misses with normalized required-term matching and reveal hidden full loss signal.

532-v518-model-capability-required-term-pair-loss-alias-focus-metrics.md
 -> v518 code explanation: carry strict and normalized loss-alias metrics directly in the focused repair report.

533-v519-model-capability-required-term-pair-loss-alias-stability-metrics.md
 -> v519 code explanation: carry strict and normalized loss-alias metrics into the seed stability report.

534-v520-model-capability-required-term-pair-loss-alias-metric-contrast.md
 -> v520 code explanation: contrast source stability metrics with focused loss-alias metrics.

535-v521-model-capability-required-term-pair-loss-alias-segment-audit.md
 -> v521 code explanation: audit newline/token segment shape behind focused loss-alias normalized hits.

536-v522-model-capability-required-term-pair-loss-alias-decode-cleanup.md
 -> v522 code explanation: audit bounded newline cleanup for focused loss-alias strict misses.

537-v523-model-capability-required-term-pair-loss-alias-focus-newline-cleanup-metrics.md
 -> v523 code explanation: carry bounded newline cleanup metrics into the main focused loss-alias report.

538-v524-model-capability-required-term-pair-loss-alias-newline-suppression-probe.md
 -> v524 code explanation: probe newline-token suppression as a strict-surface decoding fix.

## 一句话总览

本目录把 MiniGPT 后续重心从“证明训练治理链路完整”转向“用真实 tiny 训练证据观察模型能力是否变化”。
