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

594-v580-required-term-pair-branch-binding-whitespace-diagnostic.md
 -> v580 code explanation: diagnose v579 as an equals-surface whitespace first-token gap.

595-v581-required-term-pair-branch-binding-no-space-seed-3535.md
 -> v581 code explanation: test a no-space branch-binding objective on fresh seed 3535.

596-v582-required-term-pair-branch-binding-comparison.md
 -> v582 code explanation: compare v571/v579/v581 and classify branch-binding v1/v2 as regressions.

597-v583-required-term-pair-branch-binding-route-decision.md
 -> v583 code explanation: turn the branch-binding comparison into a machine-readable stop decision.

598-v584-required-term-pair-target-anchor-seed-3535.md
 -> v584 code explanation: add a target-anchor corpus mode and test seed 3535.

599-v585-required-term-pair-target-anchor-comparison.md
 -> v585 code explanation: compare target-anchor against v571/v579/v581 and keep it as residual-only.

600-v586-required-term-pair-target-anchor-route-decision.md
 -> v586 code explanation: keep target-anchor as residual evidence without promotion.

601-v587-required-term-pair-objective-closeout.md
 -> v587 code explanation: close current objectives and require a loss-branch objective next.

602-v588-required-term-pair-ten-version-closeout.md
 -> v588 code explanation: close the v579-v588 batch with full local validation.

603-v589-required-term-pair-loss-branch-objective-corpus.md
 -> v589 code explanation: add independent loss-branch objective corpus modes.

604-v590-required-term-pair-loss-branch-targeted-seed-3535.md
 -> v590 code explanation: run real seed 3535 targeted loss-branch training and record branch tradeoff.

605-v591-required-term-pair-loss-branch-dual-anchor-seed-3535.md
 -> v591 code explanation: run real seed 3535 dual-anchor loss-branch training and confirm tradeoff remains.

606-v592-required-term-pair-loss-branch-micro-span-seed-3535.md
 -> v592 code explanation: run real seed 3535 micro-span loss-branch training and confirm tradeoff remains.

607-v593-required-term-pair-loss-branch-objective-comparison.md
 -> v593 code explanation: compare v590-v592 refresh reports and confirm loss-only tradeoff.

608-v594-required-term-pair-loss-branch-route-decision.md
 -> v594 code explanation: select targeted loss-branch only as seed-stability baseline and require fixed retention.

609-v595-required-term-pair-loss-branch-targeted-seed-stability.md
 -> v595 code explanation: run 3-seed targeted loss-branch stability and confirm stable tradeoff.

610-v596-required-term-pair-loss-branch-targeted-missed-seed-diagnostic.md
 -> v596 code explanation: diagnose targeted missed seeds and identify fixed first-token retention gap.

611-v597-required-term-pair-fixed-retention-objective-readiness.md
 -> v597 code explanation: combine route decision and diagnostic into fixed-retention objective requirements.

612-v598-required-term-pair-loss-branch-batch-closeout.md
 -> v598 code explanation: close v589-v598 loss-branch batch and route toward fixed-retention objective.

613-v599-required-term-pair-fixed-retention-objective-corpus.md
 -> v599 code explanation: add fixed-retention corpus modes for the next real seed route.

614-v600-required-term-pair-fixed-retention-balanced-seed-3535.md
 -> v600 code explanation: run real balanced fixed-retention seed 3535 and record no pair-full result.

615-v601-required-term-pair-fixed-retention-first-token-seed-3535.md
 -> v601 code explanation: run real first-token fixed-retention seed 3535 and record fixed-only tradeoff.

616-v602-required-term-pair-fixed-retention-prompt-guard-seed-3535.md
 -> v602 code explanation: run real prompt-guard fixed-retention seed 3535 and record loss-only tradeoff.

617-v603-required-term-pair-fixed-retention-objective-comparison.md
 -> v603 code explanation: compare fixed-retention routes and identify v601 as fixed recovery tradeoff.

618-v604-required-term-pair-fixed-retention-route-decision.md
 -> v604 code explanation: select v601 as fixed recovery evidence and require loss rebalance.

619-v605-required-term-pair-fixed-retention-loss-rebalance-corpus.md
 -> v605 code explanation: add loss-rebalance corpus modes after fixed-only tradeoff.

620-v606-required-term-pair-fixed-retention-loss-rebalance-seed-3535.md
 -> v606 code explanation: run real loss-rebalance seed 3535 and confirm it remains loss-only.

621-v607-required-term-pair-fixed-retention-dual-cycle-seed-3535.md
 -> v607 code explanation: run real dual-cycle seed 3535 and confirm it remains fixed-only.

622-v608-required-term-pair-fixed-retention-batch-closeout.md
 -> v608 code explanation: close v599-v607 fixed-retention/loss-rebalance batch before a new objective design.

623-v609-required-term-pair-first-token-preference-diagnostic.md
 -> v609 code explanation: diagnose first-token preference conflicts across v600-v607 before new objective design.

624-v610-required-term-pair-contrast-free-objective-corpus.md
 -> v610 code explanation: add three contrast-free objective corpus modes after the first-token diagnostic.

625-v611-required-term-pair-contrast-free-seed-3535.md
 -> v611 code explanation: run real contrast-free seed 3535 and record a cross-branch negative result.

626-v612-required-term-pair-delimiter-span-seed-3535.md
 -> v612 code explanation: run real delimiter-span seed 3535 and record a fixed-only result.

627-v613-required-term-pair-context-switch-seed-3535.md
 -> v613 code explanation: run real context-switch seed 3535 and record another fixed-only result.

628-v614-required-term-pair-contrast-free-objective-comparison.md
 -> v614 code explanation: compare v611-v613 and confirm only fixed recovery, no pair-full.

629-v615-required-term-pair-contrast-free-route-decision.md
 -> v615 code explanation: stop contrast-free routes and require forced-choice diagnostics.

630-v616-required-term-pair-refresh-forced-choice-diagnostic.md
 -> v616 code explanation: add teacher-forced fixed/loss candidate scoring over refresh checkpoints.

631-v617-required-term-pair-refresh-forced-choice-diagnostic.md
 -> v617 code explanation: run forced-choice scoring over v611-v613 real checkpoints.

632-v618-required-term-pair-contrast-free-batch-closeout.md
 -> v618 code explanation: close v609-v618 contrast-free batch and route to loss internal preference objective.

633-v619-required-term-pair-loss-internal-preference-corpus.md
 -> v619 code explanation: add loss-internal-preference objective corpus modes for the next real tiny training batch.

634-v620-required-term-pair-loss-internal-preference-seed-3535.md
 -> v620 code explanation: run real loss-internal-preference seed 3535 and record a fixed-only result.

635-v621-required-term-pair-loss-internal-first-token-seed-3535.md
 -> v621 code explanation: run real loss-internal first-token seed 3535 and record a loss-only tradeoff.

636-v622-required-term-pair-loss-internal-ranked-choice-seed-3535.md
 -> v622 code explanation: run real loss-internal ranked-choice seed 3535 and record another fixed-only result.

637-v623-required-term-pair-loss-internal-preference-objective-comparison.md
 -> v623 code explanation: compare v620-v622 and confirm branch tradeoff without pair-full.

638-v624-required-term-pair-loss-internal-forced-choice-diagnostic.md
 -> v624 code explanation: run forced-choice scoring and identify v621 as an internal pair-match source.

639-v625-required-term-pair-loss-internal-preference-route-decision.md
 -> v625 code explanation: select v621 for decode bridge checks rather than promotion.

640-v626-required-term-pair-loss-internal-decode-bridge-check.md
 -> v626 code explanation: confirm the selected first-token route has a fixed generation bridge gap.

641-v627-required-term-pair-loss-internal-fixed-bridge-corpus.md
 -> v627 code explanation: add a fixed generation bridge corpus mode for the selected loss-internal route.

642-v628-required-term-pair-loss-internal-fixed-bridge-seed-3535.md
 -> v628 code explanation: run real fixed-bridge seed 3535 and confirm it restores fixed but loses loss.

643-v629-required-term-pair-loss-internal-joint-constraint-corpus.md
 -> v629 code explanation: add joint internal/generation corpus modes after the fixed-bridge tradeoff.

644-v630-required-term-pair-loss-internal-joint-cycle-seed-3535.md
 -> v630 code explanation: run real joint-cycle seed 3535 and record the first pair-full checkpoint in this route.

645-v631-required-term-pair-loss-internal-joint-cycle-forced-choice.md
 -> v631 code explanation: run forced-choice scoring for the v630 joint-cycle checkpoint and keep the result scoped.

646-v632-required-term-pair-generation-internal-alignment-comparison.md
 -> v632 code explanation: compare generation pair-full and forced-choice internal match across loss-internal routes.

647-v633-required-term-pair-generation-internal-alignment-route-decision.md
 -> v633 code explanation: turn the alignment comparison into a generation-preserving internal-repair route decision.

648-v634-required-term-pair-loss-internal-balanced-anchor-seed-3535.md
 -> v634 code explanation: run the balanced-anchor joint variant and record a fixed-only negative result.

649-v635-required-term-pair-loss-internal-balanced-anchor-forced-choice.md
 -> v635 code explanation: run forced-choice scoring for the balanced-anchor checkpoint and confirm fixed-side bias.

650-v636-required-term-pair-alignment-comparison-with-balanced-anchor.md
 -> v636 code explanation: add balanced-anchor to the generation/internal comparison and keep the v630 repair route.

651-v637-required-term-pair-route-decision-with-balanced-anchor.md
 -> v637 code explanation: re-run route decision after adding balanced-anchor and keep the joint-cycle repair route.

652-v638-required-term-pair-generation-internal-batch-closeout.md
 -> v638 code explanation: close the ten-version generation/internal batch and select joint-cycle internal repair.

653-v639-required-term-pair-joint-cycle-internal-repair-corpus.md
 -> v639 code explanation: add the joint-cycle internal-repair corpus mode selected by the v638 closeout.

654-v640-required-term-pair-joint-cycle-internal-repair-seed-3535.md
 -> v640 code explanation: run the joint-cycle internal-repair seed and record a generation regression.

655-v641-required-term-pair-joint-cycle-internal-repair-forced-choice.md
 -> v641 code explanation: run forced-choice scoring for the internal-repair checkpoint and confirm internal pair match.

656-v642-required-term-pair-alignment-comparison-with-internal-repair.md
 -> v642 code explanation: compare the internal-repair route and support zero-generation-hit negative evidence.

657-v643-required-term-pair-route-decision-with-internal-repair.md
 -> v643 code explanation: update route decision to use joint-cycle internal-repair as the current internal anchor.

658-v644-required-term-pair-joint-cycle-light-merge-corpus.md
 -> v644 code explanation: add a lighter joint-cycle merge corpus after the heavy internal-repair regression.

659-v645-required-term-pair-joint-cycle-light-merge-seed-3535.md
 -> v645 code explanation: run the joint-cycle light-merge seed and record a loss-side tradeoff.

660-v646-required-term-pair-joint-cycle-light-merge-forced-choice.md
 -> v646 code explanation: run forced-choice scoring for the light-merge checkpoint and confirm internal mismatch.

661-v647-required-term-pair-alignment-comparison-with-light-merge.md
 -> v647 code explanation: compare the light-merge route in the full generation/internal matrix.

662-v648-required-term-pair-internal-repair-batch-closeout.md
 -> v648 code explanation: close the internal-repair batch and route the next work to a two-stage schedule.

663-v649-required-term-pair-two-stage-schedule-plan.md
 -> v649 code explanation: turn the two-stage surface/internal direction into an auditable schedule contract.

664-v650-required-term-pair-surface-first-schedule-corpus.md
 -> v650 code explanation: add a runnable surface-first schedule corpus mode without claiming checkpoint resume.

665-v651-required-term-pair-surface-first-schedule-seed-3535.md
 -> v651 code explanation: run the surface-first schedule seed and record a fixed-only generation regression.

666-v652-required-term-pair-surface-first-schedule-forced-choice.md
 -> v652 code explanation: run forced-choice scoring for the surface-first checkpoint and confirm loss-side internal failure.

667-v653-required-term-pair-alignment-comparison-with-surface-first-schedule.md
 -> v653 code explanation: add surface-first schedule to the generation/internal alignment matrix.

668-v654-required-term-pair-route-decision-with-surface-first-schedule.md
 -> v654 code explanation: confirm surface-first schedule does not change the selected route.

669-v655-required-term-pair-surface-first-failure-analysis.md
 -> v655 code explanation: diagnose surface-first fixed-only collapse and select a loss-guarded follow-up.

670-v656-required-term-pair-loss-guarded-schedule-corpus.md
 -> v656 code explanation: add a loss-guarded schedule corpus mode after surface-first collapse.

671-v657-required-term-pair-loss-guarded-schedule-seed-3535.md
 -> v657 code explanation: run the loss-guarded schedule seed and record no-hit drift.

672-v658-required-term-pair-schedule-approximation-batch-closeout.md
 -> v658 code explanation: close the single-corpus schedule approximation branch as negative evidence.

673-v659-required-term-pair-refresh-resume-contract.md
 -> v659 code explanation: expose real checkpoint continuation in the required-term pair refresh wrapper.

674-v660-required-term-pair-v630-internal-repair-resume.md
 -> v660 code explanation: run real continuation from the v630 generation checkpoint into internal-repair training.

675-v661-required-term-pair-v630-internal-repair-resume-forced-choice.md
 -> v661 code explanation: run forced-choice scoring for the v630 internal-repair resumed checkpoint.

676-v662-required-term-pair-v630-light-merge-resume.md
 -> v662 code explanation: run a lower-rate light-merge continuation from the v630 generation checkpoint.

677-v663-required-term-pair-v630-light-merge-resume-forced-choice.md
 -> v663 code explanation: run forced-choice scoring for the v630 light-merge resumed checkpoint.

678-v664-required-term-pair-alignment-comparison-with-resume-routes.md
 -> v664 code explanation: fold both resume routes into the generation/internal alignment matrix and keep failed internal matches as valid negative evidence.

679-v665-required-term-pair-route-decision-with-resume-routes.md
 -> v665 code explanation: re-run route decision after adding real resume routes and keep the split-anchor strategy.

680-v666-required-term-pair-resume-branch-closeout.md
 -> v666 code explanation: generalize batch closeout wording and close the real checkpoint continuation branch as negative evidence.

681-v667-required-term-pair-v630-constrained-decode-feasibility.md
 -> v667 code explanation: run constrained decode feasibility on the v630 generation anchor and preserve the partial-gain boundary.

682-v668-required-term-pair-resume-batch-closeout.md
 -> v668 code explanation: close the v659-v668 resume/constrained-decode batch and record verification evidence.

683-v669-required-term-pair-constrained-decode-miss-diagnostic.md
 -> v669 code explanation: diagnose the remaining fixed miss after constrained decoding and route the next objective boundary.

684-v670-required-term-pair-dual-objective-boundary-plan.md
 -> v670 code explanation: turn closeout and miss diagnostic evidence into an explicit dual-objective boundary corpus plan.

685-v671-required-term-pair-dual-boundary-corpus.md
 -> v671 code explanation: register the explicit dual-objective boundary corpus mode and verify its constraints.

686-v672-required-term-pair-dual-boundary-seed-3535.md
 -> v672 code explanation: run real seed 3535 training with the explicit dual-boundary corpus and observe pair-full generation.

687-v673-required-term-pair-dual-boundary-forced-choice.md
 -> v673 code explanation: verify the dual-boundary checkpoint with forced-choice internal pair scoring.

688-v674-required-term-pair-alignment-comparison-with-dual-boundary.md
 -> v674 code explanation: compare the dual-boundary route against historical generation/internal alignment evidence.

689-v675-required-term-pair-route-decision-with-dual-boundary.md
 -> v675 code explanation: route the aligned dual-boundary candidate to multi-seed repeat before promotion.

690-v676-required-term-pair-dual-boundary-seed-stability.md
 -> v676 code explanation: add a generic aligned-candidate seed stability runner and record dual-boundary partial stability.

691-v677-required-term-pair-dual-boundary-multi-seed-forced-choice.md
 -> v677 code explanation: score the dual-boundary stability seeds internally and isolate generation-surface instability.

692-v678-required-term-pair-dual-boundary-batch-closeout.md
 -> v678 code explanation: close the dual-boundary batch as internal-stable but generation-surface unstable.

693-v679-required-term-pair-surface-failure-diagnostic.md
 -> v679 code explanation: isolate seed 2535 `loss` as the remaining internal-stable/free-generation surface failure.

694-v680-required-term-pair-surface-policy-plan.md
 -> v680 code explanation: convert the isolated surface failure into replay policies while excluding target-echo leakage.

695-v681-required-term-pair-surface-policy-replay.md
 -> v681 code explanation: replay planned surface policies over dual-boundary checkpoints and identify contextual-anchor pair-full candidates.

696-v682-required-term-pair-surface-policy-selector.md
 -> v682 code explanation: select the shorter contextual-anchor policy for minimality checks without promotion.

697-v683-required-term-pair-surface-policy-minimality-check.md
 -> v683 code explanation: verify that the selected policy requires contextual anchoring and is not promotion-ready.

698-v684-required-term-pair-surface-policy-leakage-risk.md
 -> v684 code explanation: document contextual-anchor leakage risk for the selected surface policy and keep it out of promotion claims.

699-v685-required-term-pair-surface-policy-budget-sweep.md
 -> v685 code explanation: sweep continuation budgets for the selected contextual surface policy and find the minimal stable budget.

700-v686-required-term-pair-surface-policy-execution-profile.md
 -> v686 code explanation: combine leakage-risk and budget-sweep evidence into a reusable contextual execution profile.

701-v687-required-term-pair-surface-variant-plan.md
 -> v687 code explanation: plan separator and wording variants for the contextual execution profile before real replay.

702-v688-required-term-pair-surface-variant-replay.md
 -> v688 code explanation: replay planned contextual variants over dual-boundary checkpoints and confirm all variants are stable.

703-v689-required-term-pair-surface-variant-selector.md
 -> v689 code explanation: choose the stable readable default contextual variant while preserving the no-promotion boundary.

704-v690-required-term-pair-surface-baseline-contrast.md
 -> v690 code explanation: contrast the selected contextual variant with non-leaking baselines and keep the anchor-required boundary explicit.

705-v691-required-term-pair-surface-route-decision.md
 -> v691 code explanation: close the contextual decode-aid branch and route future model work to minimal-prompt objectives.

706-v692-required-term-pair-surface-branch-closeout.md
 -> v692 code explanation: close v679-v691 as a contextual decode-aid branch with minimal-prompt capability still unsolved.

707-v693-surface-branch-final-verification.md
 -> v693 code explanation: verify the v679-v692 surface-policy batch with full tests, source encoding hygiene, and diff checks.

708-v694-minimal-prompt-objective-readiness.md
 -> v694 code explanation: convert the contextual surface branch closeout into a minimal-prompt objective readiness contract.

709-v695-minimal-prompt-corpus-contract.md
 -> v695 code explanation: register and validate the no-contextual-anchor minimal prompt equals-surface corpus contract.

710-v696-minimal-prompt-training.md
 -> v696 code explanation: run the first real minimal-prompt tiny checkpoint and preserve the loss-branch failure as negative evidence.

711-v697-minimal-prompt-branch-bias-diagnostic.md
 -> v697 code explanation: diagnose the first minimal-prompt failure as fixed-dominant branch bias.

712-v698-minimal-prompt-loss-first-token-repair-plan.md
 -> v698 code explanation: convert fixed-dominant branch-bias evidence into a loss-first-token repair corpus plan.

713-v699-minimal-prompt-loss-first-token-training.md
 -> v699 code explanation: rerun minimal-prompt training with loss-first-token repair and record the opposite branch tradeoff.

714-v700-minimal-prompt-tradeoff-comparison.md
 -> v700 code explanation: compare v696 and v699 with the existing first-token diagnostic and confirm tradeoff.

715-v701-minimal-prompt-balanced-repair-plan.md
 -> v701 code explanation: convert the minimal-prompt tradeoff into a balanced first-token repair plan.

716-v702-minimal-prompt-balanced-training.md
 -> v702 code explanation: run the balanced minimal-prompt corpus as a real tiny training negative-result check.

717-v703-minimal-prompt-batch-closeout.md
 -> v703 code explanation: close the repeated minimal-prompt training batch after three real negative-result runs.

718-v704-pair-readiness-split-plan.md
 -> v704 code explanation: convert the minimal-prompt closeout into a pair-readiness train/eval split plan.

719-v705-pair-readiness-split-contract.md
 -> v705 code explanation: materialize the pair-readiness split plan into a checked train/eval contract.

720-v706-pair-readiness-corpus-materialization.md
 -> v706 code explanation: materialize the pair-readiness split contract into a training corpus and held-out eval fixture.

721-v707-pair-readiness-training-run.md
 -> v707 code explanation: train on the materialized pair-readiness corpus and replay held-out direct probes.

722-v708-pair-readiness-heldout-failure-diagnostic.md
 -> v708 code explanation: diagnose the v707 held-out direct failure as loss prompt absorption by the fixed branch.

723-v709-pair-readiness-loss-retention-repair-plan.md
 -> v709 code explanation: convert the held-out failure diagnosis into a loss-retention repair plan.

724-v710-pair-readiness-loss-retention-contract-patch.md
 -> v710 code explanation: apply the loss-retention repair plan as a checked contract patch.

725-v711-loss-retention-corpus-materialization.md
 -> v711 code explanation: materialize the loss-retention patched contract into a larger pair-readiness corpus.

726-v712-loss-retention-training-run.md
 -> v712 code explanation: train the loss-retention patched corpus and record a no-improvement direct-probe result.

727-v713-pair-readiness-repair-comparison.md
 -> v713 code explanation: compare baseline and loss-retention pair-readiness runs and close the single-sided prefix repair route.

728-v714-pair-readiness-structured-template-contract.md
 -> v714 code explanation: convert the regressed loss-retention route into a structured prompt-answer contract for the next materialization/training pass.

729-v715-structured-template-corpus-materialization.md
 -> v715 code explanation: materialize the structured-template contract into a real pair-readiness training corpus and heldout fixture.

730-v716-structured-template-training-run.md
 -> v716 code explanation: run the structured-template corpus as a real tiny checkpoint and record its loss-only heldout direct result.

731-v717-pair-readiness-route-comparison.md
 -> v717 code explanation: compare baseline, loss-retention, and structured-template routes and classify the structured route as failure-shape change, not promotion.

732-v718-fixed-recovery-repair-plan.md
 -> v718 code explanation: convert the structured-template loss-only route comparison into a fixed-recovery repair plan.

733-v719-fixed-recovery-contract-patch.md
 -> v719 code explanation: apply the fixed-recovery plan to the structured-template contract while preserving loss rows and heldout isolation.

734-v720-fixed-recovery-corpus-materialization.md
 -> v720 code explanation: materialize the fixed-recovery patched contract into a 7040-line training corpus and heldout fixture.

735-v721-fixed-recovery-training-run.md
 -> v721 code explanation: train the fixed-recovery corpus and record that it restores fixed but loses loss again.

736-v722-four-route-comparison.md
 -> v722 code explanation: extend route comparison to four routes and close single-sided fixed/loss row patching after fixed-recovery returns to baseline.

737-v723-capacity-probe-plan.md
 -> v723 code explanation: convert the four-route closeout into a controlled larger-tiny-model capacity probe plan.

738-v724-capacity-probe-training-run.md
 -> v724 code explanation: run the larger tiny capacity probe and record that it remains fixed-only without pair-full.

739-v725-five-route-comparison.md
 -> v725 code explanation: compare baseline, repair, structured, fixed-recovery, and capacity-probe routes and close the light capacity-bump path.

740-v726-objective-structure-plan.md
 -> v726 code explanation: convert the capacity-probe no-improvement result into a checked objective-structure contract plan.

741-v727-objective-structure-contract.md
 -> v727 code explanation: build a materializable objective-structure contract with balanced task-id rows, paired blocks, and heldout leakage checks.

742-v728-objective-structure-corpus-materialization.md
 -> v728 code explanation: materialize the objective-structure contract into a 5760-line training corpus and heldout fixture.

743-v729-objective-structure-training-run.md
 -> v729 code explanation: train the objective-structure corpus and record a direct-surface mismatch negative result.

744-v730-surface-mismatch-diagnostic.md
 -> v730 code explanation: diagnose the v729 double direct miss as raw prompt surface mismatch and identify the bridge patch target.

745-v731-direct-prompt-bridge-contract-patch.md
 -> v731 code explanation: add checked raw fixed=/loss= bridge rows while preserving heldout pair isolation and materializer compatibility.

746-v732-direct-prompt-bridge-corpus-materialization.md
 -> v732 code explanation: materialize the direct-prompt bridge contract patch into an 8320-line corpus and heldout fixture.

747-v733-direct-prompt-bridge-training-run.md
 -> v733 code explanation: train the direct-prompt bridge corpus and record that it still has zero direct hits with renewed fixed pollution.

748-v734-bridge-comparison.md
 -> v734 code explanation: compare v729 and v733, close the bridge route after no hit improvement and introduced fixed pollution.

749-v735-bridge-closeout-plan.md
 -> v735 code explanation: close the no-improvement bridge route and plan a direct-completion surface contract.

750-v736-direct-completion-surface-contract.md
 -> v736 code explanation: build a materializer-ready direct-completion surface contract with balanced fixed/loss exact rows, prefix ladders, and heldout pair isolation.

751-v737-direct-completion-surface-corpus-materialization.md
 -> v737 code explanation: materialize the direct-completion surface contract into a 5120-line corpus and heldout fixture.

752-v738-direct-completion-surface-training-run.md
 -> v738 code explanation: train the direct-completion surface corpus and record pair-full heldout direct evidence under the same larger-tiny configuration.

753-v739-direct-completion-route-comparison.md
 -> v739 code explanation: compare objective-structure, direct-prompt bridge, and direct-completion surface training routes and select direct-completion as a candidate for stricter replay.

754-v740-direct-completion-pair-probe-replay.md
 -> v740 code explanation: replay the selected direct-completion checkpoint on heldout pair prompt surfaces and mark the route as direct-probe-only after pair prompts do not transfer.

755-v741-pair-prompt-transfer-repair-plan.md
 -> v741 code explanation: turn the pair-probe replay failure into a non-leaking pair prompt transfer contract patch plan.

756-v742-pair-prompt-transfer-contract-patch.md
 -> v742 code explanation: add non-heldout pair-transfer rows to the direct-completion surface contract and register the patch with materialization.

757-v743-pair-prompt-transfer-corpus-materialization.md
 -> v743 code explanation: materialize the pair prompt transfer contract patch into a 7680-line training corpus and heldout fixture without leaking the exact pair prompt.

758-v744-pair-prompt-transfer-training-run.md
 -> v744 code explanation: train the pair prompt transfer corpus and record the loss-only negative result under the same larger-tiny settings.

759-v745-pair-prompt-transfer-regression-diagnostic.md
 -> v745 code explanation: compare v738, v740, and v744 evidence to close the regressed full surrogate transfer patch route.

760-v746-fixed-preserving-transfer-plan.md
 -> v746 code explanation: turn the transfer regression closeout into a four-row-budget fixed-preserving contract patch plan.

761-v747-fixed-preserving-transfer-contract-patch.md
 -> v747 code explanation: apply the fixed-preserving plan as a checked four-row contract patch and register it for materialization.

762-v748-fixed-preserving-transfer-corpus-materialization.md
 -> v748 code explanation: materialize the fixed-preserving transfer contract patch into a 6400-line corpus and heldout fixture.

763-v749-fixed-preserving-transfer-training-run.md
 -> v749 code explanation: train the fixed-preserving corpus under the larger-tiny settings and record the direct pair-probe hit before independent replay.

764-v750-fixed-preserving-transfer-pair-probe-replay.md
 -> v750 code explanation: independently replay the v749 checkpoint and record partial pair-probe evidence before any promotion.

765-v751-prompt-surface-sensitivity-diagnostic.md
 -> v751 code explanation: combine v749 training and v750 replay evidence to diagnose prompt-surface sensitivity and block promotion.

766-v752-exact-surface-repair-plan.md
 -> v752 code explanation: turn prompt-surface sensitivity into a bounded exact-surface repair plan without leaking the heldout prompt.

767-v753-exact-surface-repair-contract-patch.md
 -> v753 code explanation: apply the exact-surface plan as a checked four-row contract patch and register it for materialization.

768-v754-exact-surface-repair-corpus-materialization.md
 -> v754 code explanation: materialize the exact-surface repair contract patch into a 7680-line corpus without heldout leakage.

769-v755-exact-surface-repair-training-run.md
 -> v755 code explanation: train the exact-surface repair corpus and record direct pair-probe hit evidence before independent replay.

770-v756-exact-surface-repair-pair-probe-replay.md
 -> v756 code explanation: independently replay the exact-surface repair checkpoint and record the partial, non-promotable result.

771-v757-exact-surface-repair-effectiveness-comparison.md
 -> v757 code explanation: compare v750 and v756 replay surfaces and close the ineffective near-exact repair route.

772-v758-exact-surface-repair-route-closeout.md
 -> v758 code explanation: convert the ineffective exact-surface repair comparison into a closed-route boundary and next-route candidates.

773-v759-objective-or-decoding-alternative-selector.md
 -> v759 code explanation: score objective, decoding, and fresh-seed alternatives after v758 closeout and select objective-level contrast.

774-v760-objective-level-contrast-plan.md
 -> v760 code explanation: turn the selected objective-level contrast route into a contract design plan with heldout boundaries.

775-v761-objective-level-contrast-contract.md
 -> v761 code explanation: materialize the objective-level contrast plan into a 26-row contract and register it with corpus materialization.

776-v762-objective-level-contrast-corpus-materialization.md
 -> v762 code explanation: materialize the objective-level contrast contract into an 8320-line corpus and heldout fixture.

777-v763-objective-level-contrast-training-run.md
 -> v763 code explanation: train the objective-level contrast corpus and record direct pair-probe hit evidence before independent replay.

778-v764-objective-level-contrast-pair-probe-replay.md
 -> v764 code explanation: independently replay the v763 checkpoint across exact, spaced, and arrow pair prompts and record all pair-full evidence.

779-v765-objective-level-contrast-route-comparison.md
 -> v765 code explanation: compare baseline, near-exact repair, and objective-level contrast replay routes and select the objective route for promotion guards.

780-v766-objective-level-contrast-promotion-guard.md
 -> v766 code explanation: run a guarded promotion check that allows seed stability but blocks single-seed acceptance.

781-v767-objective-level-contrast-seed-stability-plan.md
 -> v767 code explanation: turn the guarded route candidate into a concrete supplemental-seed stability plan.

782-v768-objective-level-contrast-seed-3737-training-run.md
 -> v768 code explanation: train the first supplemental objective-level contrast seed and keep the result pending replay.

783-v769-objective-level-contrast-seed-3737-pair-probe-replay.md
 -> v769 code explanation: replay the first supplemental objective-level contrast seed and record the passing but weaker pair-full count.

784-v770-objective-level-contrast-seed-3838-training-run.md
 -> v770 code explanation: train the second supplemental objective-level contrast seed with unchanged corpus and model settings.

785-v771-objective-level-contrast-seed-3838-pair-probe-replay.md
 -> v771 code explanation: replay the second supplemental objective-level contrast seed and complete the seed-stability replay inputs.

786-v772-objective-level-contrast-seed-stability-rollup.md
 -> v772 code explanation: roll up three objective-level contrast seed replays into an acceptance-review-ready candidate while keeping promotion gated.

787-v773-receipt-validation-split.md
 -> v773 code explanation: split promoted seed handoff receipt schema validation out of the largest receipt workflow module.

788-v774-handoff-review-recommendations-split.md
 -> v774 code explanation: extract handoff review recommendation text and detail generation from the core review builder.

789-v775-promoted-comparison-recommendations-split.md
 -> v775 code explanation: extract promoted training-scale comparison recommendation text from the comparison builder.

790-v776-receipt-outputs-split.md
 -> v776 code explanation: extract promoted seed handoff receipt text renderers from the receipt workflow module.

791-v777-release-readiness-comparison-narrative-split.md
 -> v777 code explanation: extract release readiness comparison narrative wording from the comparison workflow.

792-v778-release-readiness-comparison-regression-split.md
 -> v778 code explanation: extract release readiness comparison regression scoring from the comparison workflow.

793-v779-maturity-narrative-release-summary-split.md
 -> v779 code explanation: extract maturity narrative release-context normalization from the portfolio summary workflow.

794-v780-release-readiness-panel-split.md
 -> v780 code explanation: extract release readiness dashboard panel builders from the dashboard workflow.

## 一句话总览

本目录把 MiniGPT 后续重心从“证明训练治理链路完整”转向“用真实 tiny 训练证据观察模型能力是否变化”。
