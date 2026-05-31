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

539-v525-model-capability-required-term-pair-loss-alias-newline-suppression-repeat.md
 -> v525 code explanation: repeat newline-suppressed decoding across v518 and v523 focus checkpoints.

540-v526-generator-blocked-token-profile.md
 -> v526 code explanation: promote newline suppression into the core generator as an optional blocked-token profile.

541-v527-model-capability-required-term-pair-loss-alias-blocked-token-fresh-compare.md
 -> v527 code explanation: compare blocked-token decoding against a freshly trained loss-alias focus checkpoint.

542-v528-model-capability-required-term-pair-loss-alias-fresh-seed-sweep.md
 -> v528 code explanation: run a three-seed fresh sweep and compare baseline strict coverage against blocked-token coverage.

543-v529-generation-profile-surface.md
 -> v529 code explanation: expose newline-suppression decoding as a named CLI/API/playground generation profile.

544-v530-generation-profiles-endpoint.md
 -> v530 code explanation: publish generation profiles through a runtime server endpoint and reload them in playground.

545-v531-generation-profile-contract-check.md
 -> v531 code explanation: verify endpoint, health, API, CLI, and playground artifacts for the generation profile contract.

546-v532-required-term-pair-generation-profile-replay.md
 -> v532 code explanation: replay default and newline-suppression profiles over archived fixed/loss pair checkpoints.

547-v533-required-term-pair-coexistence-refresh.md
 -> v533 code explanation: train a tiny fixed/loss coexistence refresh checkpoint and replay generation profiles.

548-v534-required-term-pair-first-token-preference.md
 -> v534 code explanation: diagnose first-token logits for the v533 fixed/loss refresh checkpoint.

549-v535-required-term-pair-colon-immediate-refresh.md
 -> v535 code explanation: train colon-immediate fixed/loss rows and confirm the first-token whitespace drift disappears.

550-v536-required-term-pair-colon-immediate-stability.md
 -> v536 code explanation: repeat the colon-immediate fixed/loss refresh across seeds and classify partial stability.

551-v537-required-term-pair-colon-immediate-missed-seed-diagnostic.md
 -> v537 code explanation: diagnose v536 missed seeds with first-token logits and identify the preference gap.

552-v538-required-term-pair-first-token-boost-stability.md
 -> v538 code explanation: test a first-token boost corpus and preserve the negative stability result.

553-v539-required-term-pair-isolated-prompt-stability.md
 -> v539 code explanation: test isolated prompt blocks and record why the direction regressed.

554-v540-required-term-pair-direct-budget-stability.md
 -> v540 code explanation: run a higher-budget direct mapping check and rule out simple under-training.

555-v541-required-term-pair-decode-boundary-check.md
 -> v541 code explanation: replay v540 checkpoints across decode boundaries and recover one fixed/loss pair seed with wider top-k.

556-v542-required-term-pair-topk2-stability.md
 -> v542 code explanation: promote the v541 top-k2 finding into the full colon-immediate stability runner.

557-v543-required-term-pair-temperature-boundary-check.md
 -> v543 code explanation: parameterize decode specs and find the top-k2 temperature boundary that recovers two seeds.

558-v544-required-term-pair-topk2-t080-stability.md
 -> v544 code explanation: promote top-k2 temperature decoding into formal stability and reach two recovered seeds.

559-v545-required-term-pair-first-token-boost-topk2-t080.md
 -> v545 code explanation: test first-token boost under the best decode setting and preserve the negative result.

560-v546-required-term-pair-loss-calibrated-topk2-t080.md
 -> v546 code explanation: add a loss-calibrated corpus mode and expose the seed coverage tradeoff.

561-v547-required-term-pair-seed-coverage-tradeoff.md
 -> v547 code explanation: compare v544/v546 stability reports and formalize seed-level coverage tradeoff.

562-v548-required-term-pair-seed-config-selection.md
 -> v548 code explanation: derive and verify a deterministic per-seed config-selection policy.

563-v549-required-term-pair-seed-config-replay.md
 -> v549 code explanation: reconnect selected policy to source checkpoints and replay each selected seed/config.

564-v550-required-term-pair-seed-config-heldout-replay.md
 -> v550 code explanation: test selected configs against held-out prompt surfaces and isolate the equals/1535 gap.

565-v551-required-term-pair-seed-config-heldout-gap.md
 -> v551 code explanation: diagnose the v550 equals/1535 miss down to a fixed-term surface gap.

566-v552-required-term-pair-equals-surface-fixed-repair.md
 -> v552 code explanation: add an equals-surface fixed repair corpus mode and preserve its negative real-training result.

567-v553-required-term-pair-coexistence-corpus-split.md
 -> v553 code explanation: split required-term pair corpus design out of the refresh executor.

568-v554-required-term-pair-equals-surface-balanced-repair.md
 -> v554 code explanation: test a balanced equals-surface repair and preserve the branch-competition negative result.

569-v555-required-term-pair-equals-surface-repair-comparison.md
 -> v555 code explanation: compare v552/v554 equals-surface repairs and formalize the branch-competition diagnosis.

570-v556-required-term-pair-equals-surface-tied-repair.md
 -> v556 code explanation: add a tied equals-surface corpus mode and preserve the negative seed 1535 result.

571-v557-required-term-pair-refresh-forced-choice.md
 -> v557 code explanation: score fixed/loss candidate continuations on the v556 refresh checkpoint and diagnose preference collapse.

572-v558-required-term-pair-constrained-decode-feasibility.md
 -> v558 code explanation: test competing-initial decode constraints and reject decode-only mitigation for the v556 checkpoint.

573-v559-required-term-pair-equals-surface-tied-wider-embd.md
 -> v559 code explanation: rerun tied equals-surface repair with wider embedding and record the capacity-negative result.

574-v560-required-term-pair-equals-surface-no-pair-id-repair.md
 -> v560 code explanation: remove pair-id equals competition from tied repair and record the fixed-only partial recovery.

575-v561-required-term-pair-equals-surface-no-pair-id-loss-balanced-repair.md
 -> v561 code explanation: add loss-balanced no-pair-id objective and recover seed 1535 pair-full.

576-v562-required-term-pair-equals-surface-no-pair-id-loss-balanced-stability.md
 -> v562 code explanation: replay the loss-balanced no-pair-id objective across three seeds and classify the result as partial stability.

577-v563-required-term-pair-no-pair-id-loss-balanced-missed-seed-diagnostic.md
 -> v563 code explanation: diagnose v562 missed seeds and locate the remaining gap at first-token preference.

578-v564-required-term-pair-no-pair-id-loss-balanced-first-token-stability.md
 -> v564 code explanation: add explicit first-token prefix rows and preserve the mixed three-seed result.

579-v565-required-term-pair-no-pair-id-first-token-migration-comparison.md
 -> v565 code explanation: compare v562 and v564 to classify first-token rows as coverage migration rather than stable gain.

580-v566-required-term-pair-no-pair-id-loss-balanced-light-first-token-stability.md
 -> v566 code explanation: test sparse first-token bridge hints and preserve the 0/3 negative result.

581-v567-required-term-pair-no-pair-id-first-token-density-comparison.md
 -> v567 code explanation: compare v562/v564/v566 first-token hint density and stop that route as unstable coverage migration.

582-v568-required-term-pair-first-token-route-decision.md
 -> v568 code explanation: turn v567 comparison evidence into a stop-first-token-density route decision.

583-v569-required-term-pair-route-heldout-replay.md
 -> v569 code explanation: replay the selected v562-loss-balanced route on held-out prompt surfaces.

584-v570-required-term-pair-route-heldout-expanded-suite.md
 -> v570 code explanation: expand the route held-out replay suite to seven prompt surfaces.

585-v571-required-term-pair-route-fresh-seed-3535.md
 -> v571 code explanation: rerun the selected route on fresh seed 3535 and preserve the negative stability result.

586-v572-required-term-pair-route-fresh-seed-3535-missed-diagnostic.md
 -> v572 code explanation: diagnose fresh seed 3535 as a loss-branch first-token preference gap.

587-v573-required-term-pair-route-fresh-seed-3535-first-token-repair.md
 -> v573 code explanation: test the existing full first-token repair mode on fresh seed 3535 and preserve the negative result.

588-v574-required-term-pair-route-fresh-seed-3535-repair-comparison.md
 -> v574 code explanation: compare v571/v573 and classify full first-token repair as a regression route for fresh seed 3535.

589-v575-required-term-pair-route-fresh-seed-3535-wider-embd.md
 -> v575 code explanation: test n_embd=96 on fresh seed 3535 and rule out simple width scaling.

590-v576-required-term-pair-route-fresh-seed-3535-variable-comparison.md
 -> v576 code explanation: compare v571/v573/v575 and reject first-token rows plus width scaling for seed 3535.

591-v577-required-term-pair-fresh-seed-route-decision.md
 -> v577 code explanation: turn the v576 variable comparison into a machine-readable route stop decision.

592-v578-required-term-pair-route-closeout-summary.md
 -> v578 code explanation: close the v569-v577 route batch before starting a branch-binding objective.

593-v579-required-term-pair-branch-binding-seed-3535.md
 -> v579 code explanation: add split branch-binding corpus mode and preserve the first fresh-seed baseline.

## 一句话总览

本目录把 MiniGPT 后续重心从“证明训练治理链路完整”转向“用真实 tiny 训练证据观察模型能力是否变化”。
