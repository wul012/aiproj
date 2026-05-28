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

323-v309-promoted-training-scale-comparison-ci-regression-context.md
 -> v309 code explanation: carry promotion-index handoff CI regression evidence into promoted comparisons, per-row exclusion reasons, and stale compare-ready rechecks.

324-v310-promoted-training-scale-decision-ci-regression-context.md
 -> v310 code explanation: carry promoted-comparison CI regression exclusions into promoted baseline decisions, rejected candidates, outputs, and CLI diagnostics.

325-v311-promoted-training-scale-seed-ci-regression-context.md
 -> v311 code explanation: carry promoted-decision CI regression exclusions into promoted next-cycle seeds, seed outputs, and CLI diagnostics.

326-v312-promoted-training-scale-seed-handoff-ci-regression-context.md
 -> v312 code explanation: carry promoted-seed CI regression exclusions into final seed handoff outputs, automation receipt, CLI diagnostics, and strict clean-batch gating.

327-v313-promoted-seed-handoff-receipt-ci-contract.md
 -> v313 code explanation: upgrade promoted seed handoff automation receipts to schema v2 and validate CI-regression fields in receipt and embedded sidecar checks.

328-v314-promoted-seed-handoff-assurance-ci-contract-summary.md
 -> v314 code explanation: lift schema-v2 receipt CI-regression contract fields into embedded receipt checks, handoff assurance, and CI smoke summaries.

329-v315-tiny-standard-benchmark-smoke.md
 -> v315 code explanation: add a CPU tiny train, standard-suite eval, generation-quality, and benchmark-scorecard smoke to separate evidence readiness from model quality claims.

330-v316-tiny-standard-pair-baseline-smoke.md
 -> v316 code explanation: add same-checkpoint pair-batch evidence to the CPU tiny standard benchmark smoke and keep it labeled as reproducibility evidence, not model improvement.

331-v317-tiny-scorecard-comparison-smoke.md
 -> v317 code explanation: run two real tiny benchmark smokes, compare their scorecards, and keep the result framed as comparison plumbing evidence rather than model-quality proof.

332-v318-tiny-scorecard-decision-smoke.md
 -> v318 code explanation: extend the tiny scorecard comparison smoke through benchmark scorecard decision artifacts while keeping blocked/review/promote statuses as decision evidence, not model-quality proof.

333-v319-tiny-decision-diagnostics-smoke.md
 -> v319 code explanation: lift blocked/review candidate names, first blockers, review items, and recommendations from decision JSON into the tiny smoke summary for CI-readable diagnostics.

334-v320-tiny-budget-comparison-smoke.md
 -> v320 code explanation: let the tiny scorecard comparison smoke run baseline and candidate with different training budgets and persist that budget mode in summary evidence.

335-v321-promoted-seed-handoff-artifact-split.md
 -> v321 code explanation: split promoted seed handoff receipt/check/assurance artifact helpers into a dedicated receipt artifact module while keeping the public handoff API stable.

336-v322-tiny-decision-threshold-smoke.md
 -> v322 code explanation: make the tiny scorecard comparison smoke promotion threshold configurable and persist the threshold in run config, text summary, and real smoke evidence.

337-v323-tiny-threshold-diagnostics-smoke.md
 -> v323 code explanation: expose the first threshold-blocked candidate, rubric score, configured threshold, and score margin in the tiny scorecard comparison smoke summary.

338-v324-tiny-threshold-profile-smoke.md
 -> v324 code explanation: expand tiny threshold diagnostics into threshold-blocked counts, candidate names, closest-to-pass margin, and largest-gap margin.

339-v325-decision-threshold-profile-artifact.md
 -> v325 code explanation: move threshold profiles into benchmark scorecard decision summaries and render them through decision JSON, Markdown, HTML, and tiny smoke summaries.

340-v326-decision-failure-taxonomy.md
 -> v326 code explanation: classify benchmark scorecard decision blockers and review items into stable categories, aggregate dominant failure modes, and expose them through artifacts and tiny smoke summaries.

341-v327-decision-remediation-plan.md
 -> v327 code explanation: map benchmark scorecard decision failure taxonomy counts into structured remediation actions and expose the first action through tiny smoke summaries.

342-v328-remediation-summary.md
 -> v328 code explanation: lift remediation plan count, blocker/review distribution, and dominant remediation action into decision and tiny smoke summaries.

343-v329-remediation-metadata.md
 -> v329 code explanation: enrich remediation plan rows with action code, severity, owner scope, and target artifacts for script and reviewer consumption.

344-v330-remediation-csv-artifact.md
 -> v330 code explanation: export remediation plan rows as a standalone CSV artifact and include it in tiny smoke artifact status.

345-v331-clean-remediation-gate.md
 -> v331 code explanation: add an opt-in clean remediation gate to the tiny scorecard comparison smoke so strict runs can stop on remaining remediation rows.

346-v332-remediation-gate-issues.md
 -> v332 code explanation: add machine-readable issue rows to the clean remediation gate and keep strict smoke failures easy for CI to classify.

347-v333-remediation-gate-issue-text.md
 -> v333 code explanation: mirror the first clean-remediation gate issue fields into the text summary for shell-only CI readers.

348-v334-tiny-scorecard-smoke-checker.md
 -> v334 code explanation: add a reusable checker for completed tiny scorecard comparison smoke summaries, including artifact, gate, command, and model-quality-claim boundaries.

349-v335-inline-tiny-scorecard-smoke-check.md
 -> v335 code explanation: embed the reusable tiny scorecard summary checker into the smoke command as optional sidecar output.

350-v336-ci-tiny-scorecard-inline-check.md
 -> v336 code explanation: promote the inline tiny scorecard summary-check smoke into GitHub Actions and CI workflow hygiene.

351-v337-ci-tiny-scorecard-wrapper.md
 -> v337 code explanation: wrap the CI tiny scorecard inline smoke in a stable GitHub Actions entrypoint while keeping the fixed budget testable in code.

352-v338-ci-tiny-scorecard-plan-artifacts.md
 -> v338 code explanation: persist CI tiny scorecard wrapper invocation plans as JSON/text artifacts with fixed budget, command, sidecar path, and return code.

353-v339-ci-tiny-scorecard-plan-digests.md
 -> v339 code explanation: add summary and summary-check artifact sha256 digests to CI tiny scorecard wrapper invocation plans.

354-v340-ci-tiny-scorecard-plan-checker.md
 -> v340 code explanation: add a reusable checker that revalidates CI tiny scorecard wrapper plan artifact digests without rerunning training.

355-v341-ci-tiny-scorecard-plan-digest-gate.md
 -> v341 code explanation: promote the CI tiny scorecard plan digest checker into GitHub Actions and CI workflow hygiene order rules.

356-v342-ci-tiny-scorecard-plan-digest-summary.md
 -> v342 code explanation: lift the CI tiny scorecard plan digest gate into CI workflow hygiene summary fields and project audit context.

357-v343-benchmark-history-ledger.md
 -> v343 code explanation: connect scorecard comparison and decision artifacts into a reusable benchmark history ledger with history-ready outputs and boundary labels.

358-v344-benchmark-history-maturity-narrative.md
 -> v344 code explanation: let maturity narrative consume benchmark history ledgers and turn history regressions into portfolio review signals.

359-v345-benchmark-history-project-audit.md
 -> v345 code explanation: let project audit consume benchmark history ledgers and expose history readiness, regressions, quality-claim boundaries, and latest boundary in audit evidence.

360-v346-benchmark-history-release-bundle.md
 -> v346 code explanation: let release bundles carry benchmark history context from project audit and preserve history readiness, regression, quality-claim, and boundary evidence in release handoff.

361-v347-benchmark-history-release-gate.md
 -> v347 code explanation: let release gates and release gate profile comparisons consume benchmark history evidence so release decisions expose missing, warning, blocked, regression, and legacy-override boundaries.

362-v348-benchmark-history-release-readiness.md
 -> v348 code explanation: carry benchmark history gate and bundle boundaries into release readiness summary, panel, CLI, Markdown, and HTML outputs.

363-v349-benchmark-history-readiness-comparison.md
 -> v349 code explanation: compare release readiness benchmark-history status, regression, quality-claim, and boundary deltas across baseline and candidate dashboards.

364-v350-registry-benchmark-readiness-tracking.md
 -> v350 code explanation: carry release-readiness benchmark-history regression evidence into registry summaries, rows, leaderboards, CSV, HTML, and CLI output.

365-v351-maturity-benchmark-readiness-carryover.md
 -> v351 code explanation: carry registry benchmark-history readiness regressions into maturity summary, maturity narrative, CLI diagnostics, and review decisions.

366-v352-dataset-dedupe-snapshots.md
 -> v352 code explanation: add opt-in exact-source dedupe, reproducible dataset snapshots, and dataset card snapshot evidence for prepared corpora.

367-v353-dataset-version-comparison.md
 -> v353 code explanation: compare prepared dataset versions, snapshot deltas, dedupe policies, source-order digests, and included/skipped source changes before model promotion review.

368-v354-run-comparison-dataset-snapshot.md
 -> v354 code explanation: carry dataset snapshot deltas into run comparison so model/loss deltas can be reviewed beside data-boundary changes.

369-v355-registry-dataset-snapshot.md
 -> v355 code explanation: carry dataset snapshot evidence into registry rows, summaries, CSV/SVG/HTML, and CLI output for multi-run data-boundary review.

370-v356-model-card-dataset-snapshot.md
 -> v356 code explanation: carry registry dataset snapshot evidence into model cards so project-level summaries preserve data-boundary review context.

371-v357-governance-stabilization-review.md
 -> v357 code explanation: add a maintenance-policy governance stabilization review that pauses new chains and watches the current seven for overlap before expansion.

372-v358-governance-stabilization-reasons.md
 -> v358 code explanation: require review reasons and expansion rules for the seven governance chains before future expansion.

373-v359-governance-proposal-routing.md
 -> v359 code explanation: route governance proposals into the existing seven chains first, with review and reject paths for unmatched or high-risk items.

374-v360-governance-routing-basis.md
 -> v360 code explanation: record whether proposal routing matched by exact chain id or keyword match and surface that basis in reports and CLI output.

375-v361-governance-routing-keyword-hit.md
 -> v361 code explanation: carry the specific keyword hit used by keyword-based governance routing into reports, CLI stdout, and evidence artifacts.

376-v362-governance-ambiguous-keyword-review.md
 -> v362 code explanation: review proposals whose keywords match multiple governance chains instead of auto-merging them into the first match.

377-v363-governance-routing-gate.md
 -> v363 code explanation: add an opt-in clean governance routing gate that can stop CLI runs on review-required or ambiguous proposals.

378-v364-benchmark-history-readiness-gate.md
 -> v364 code explanation: add a benchmark-history readiness gate before treating model-evaluation history as promotion-ready evidence.

379-v365-maturity-benchmark-readiness-consumption.md
 -> v365 code explanation: consume benchmark-history readiness requirements inside maturity narrative portfolio review.

380-v366-project-audit-benchmark-readiness.md
 -> v366 code explanation: consume benchmark-history readiness requirements inside project audit checks, summaries, CLI, and reports.

381-v367-release-bundle-benchmark-readiness.md
 -> v367 code explanation: consume benchmark-history readiness requirements inside release bundle handoff and stale-audit review decisions.

382-v368-release-gate-benchmark-readiness.md
 -> v368 code explanation: consume benchmark-history readiness requirements inside release gate checks, summaries, CLI output, and reports.

383-v369-release-readiness-benchmark-requirement.md
 -> v369 code explanation: carry benchmark-history readiness requirements into release readiness dashboards and readiness comparison regressions.

384-v370-registry-benchmark-requirement.md
 -> v370 code explanation: carry benchmark-history readiness requirement regressions into registry rows, summaries, leaderboard rendering, CSV, and CLI output.

385-v371-maturity-benchmark-requirement-carryover.md
 -> v371 code explanation: carry benchmark-history readiness requirement changes into maturity summary, maturity narrative, CLI diagnostics, and review decisions.

386-v372-maintenance-split-consolidation.md
 -> v372 code explanation: consolidate release bundle, governance stabilization, and promoted seed handoff artifact boundaries without changing public output contracts.

387-v373-benchmark-requirement-reason-drift.md
 -> v373 code explanation: carry benchmark-history readiness failed-reason additions through release readiness comparison, registry, maturity summary, and maturity narrative review.

388-v374-registry-release-readiness-split.md
 -> v374 code explanation: split registry release-readiness delta aggregation into a dedicated module and carry failed-reason removals as visible recovery evidence.

389-v375-benchmark-reason-recovery-signal.md
 -> v375 code explanation: promote failed-reason removals into explicit recovery drift status and recovery counts across comparison, registry, maturity, and narrative outputs.

390-v376-benchmark-reason-mixed-drift.md
 -> v376 code explanation: expose mixed benchmark readiness failed-reason drift as its own review signal across comparison, registry, maturity, narrative, CLI, and artifact outputs.

391-v377-release-readiness-drift-contract.md
 -> v377 code explanation: validate release readiness failed-reason drift delta and summary fields against their source baseline/compared reason lists.

392-v378-release-readiness-drift-contract-ci-smoke.md
 -> v378 code explanation: promote release readiness drift contract validation into CI with a stable mixed-drift smoke fixture and workflow hygiene guard.

393-v379-release-readiness-drift-smoke-readiness.md
 -> v379 code explanation: expose release readiness drift-contract smoke readiness through CI hygiene, project audit, release bundle, and release readiness evidence.

394-v380-release-readiness-drift-smoke-comparison.md
 -> v380 code explanation: compare release readiness drift-contract smoke readiness across baseline and candidate dashboards and treat ready-to-not-ready as CI workflow regression evidence.

395-v381-release-readiness-ci-regression-reasons.md
 -> v381 code explanation: classify CI workflow regressions in release readiness comparison with machine-readable reasons and reason-count recommendations.

396-v382-registry-release-readiness-ci-reasons.md
 -> v382 code explanation: carry release readiness CI regression reasons into registry rows, summaries, CLI output, CSV, HTML, and leaderboard evidence.

397-v383-maturity-release-readiness-ci-reasons.md
 -> v383 code explanation: carry registry release readiness CI regression reasons into maturity summary, maturity narrative, rendered outputs, CLI fields, and review recommendations.

398-v384-training-portfolio-maturity-ci-reasons.md
 -> v384 code explanation: carry maturity narrative CI regression reasons into training portfolio comparison summaries, review actions, recommendations, CSV, Markdown, and HTML evidence.

399-v385-training-portfolio-batch-maturity-ci-reasons.md
 -> v385 code explanation: carry training portfolio comparison maturity CI regression reason counts into batch review summaries, rendered outputs, and CLI evidence.

400-v386-training-scale-run-maturity-ci-reasons.md
 -> v386 code explanation: carry batch maturity CI regression reason counts into gated training scale run summaries, rendered outputs, and CLI evidence.

401-v387-training-scale-run-comparison-maturity-ci-reasons.md
 -> v387 code explanation: carry gated scale-run maturity CI regression reason counts into multi-run comparison summaries, rendered outputs, and CLI evidence.

402-v388-training-scale-run-decision-maturity-ci-reasons.md
 -> v388 code explanation: carry scale-run comparison maturity CI regression reason counts into run decisions and consolidate reason-count helper parsing/formatting.

403-v389-workflow-handoff-maturity-ci-reasons.md
 -> v389 code explanation: carry training scale decision maturity CI regression reason counts into workflow and handoff summaries, rendered outputs, CLI logs, and review recommendations.

404-v390-training-scale-promotion-maturity-ci-reasons.md
 -> v390 code explanation: carry workflow/handoff maturity CI regression reason counts into training scale promotion summaries, rendered outputs, CLI logs, and promotion review recommendations.

405-v391-training-scale-promotion-index-maturity-ci-reasons.md
 -> v391 code explanation: carry promotion maturity CI regression reason counts into promotion-index rows, summary aggregation, rendered outputs, CLI logs, and comparison-readiness recommendations.

406-v392-promoted-training-scale-comparison-maturity-ci-reasons.md
 -> v392 code explanation: carry promotion-index maturity CI regression reason counts into promoted-comparison rows, summary aggregation, rendered outputs, CLI logs, and exclusion recommendations.

407-v393-promoted-training-scale-decision-maturity-ci-reasons.md
 -> v393 code explanation: carry promoted-comparison maturity CI regression reason counts into baseline decision summaries, rendered outputs, CLI logs, and review recommendations.

408-v394-promoted-training-scale-seed-maturity-ci-reasons.md
 -> v394 code explanation: carry promoted-decision maturity CI regression reason counts into next-cycle seed summaries, rendered outputs, CLI logs, and seed recommendations.

409-v395-promoted-training-scale-seed-section-split.md
 -> v395 code explanation: split promoted seed HTML section rendering out of the artifact writer while preserving public render/write/export behavior.

410-v396-promoted-training-scale-seed-handoff-maturity-ci-reasons.md
 -> v396 code explanation: carry promoted seed maturity CI regression reason counts into final seed handoff summaries, requirements, rendered outputs, CLI logs, and recommendations.

411-v397-governance-chain-value-review.md
 -> v397 code explanation: add value status, duplicate-risk, recent-expansion, and freeze-new-fields guardrails to the existing seven-chain governance stabilization review.

412-v398-tiny-scorecard-benchmark-history.md
 -> v398 code explanation: make the tiny scorecard comparison smoke write benchmark-history artifacts and preserve the tiny-smoke readiness boundary in summary and CLI output.

413-v399-ci-benchmark-history-plan-digest.md
 -> v399 code explanation: include benchmark-history artifacts in the CI tiny scorecard wrapper plan digest and plan checker.

414-v400-ci-benchmark-history-semantic-boundary.md
 -> v400 code explanation: parse benchmark-history semantics in the CI plan checker and protect the tiny-smoke boundary.

415-v401-ci-wrapper-benchmark-history-summary.md
 -> v401 code explanation: write benchmark-history semantic summaries into the CI tiny scorecard wrapper plan and text output.

416-v402-eval-suite-design-coverage.md
 -> v402 code explanation: add prompt-suite design coverage summaries and carry them into the tiny standard benchmark smoke.

417-v403-tiny-scorecard-comparison-smoke-summary-output-split.md
 -> v403 code explanation: split the 766-line tiny scorecard comparison smoke into summary computation and output rendering modules while keeping the CLI wrapper and test contract unchanged.

418-v404-maintenance-policy-engine-split.md
 -> v404 code explanation: split the maintenance policy engine into common helpers, batching policy, and governance review modules while preserving the public facade.

419-v405-eval-suite-design-report.md
 -> v405 code explanation: carry prompt-suite design summaries into general eval suite JSON and HTML reports.

420-v406-benchmark-scorecard-suite-design-readiness.md
 -> v406 code explanation: carry eval suite design readiness into benchmark scorecards and scorecard comparisons.

421-v407-benchmark-decision-suite-design-remediation.md
 -> v407 code explanation: carry suite-design readiness into benchmark scorecard promotion decisions and remediation.

422-v408-benchmark-history-suite-design-readiness.md
 -> v408 code explanation: carry suite-design readiness into the benchmark history ledger so the history layer records both eval and design comparison readiness.

423-v409-maturity-narrative-history-suite-design.md
 -> v409 code explanation: carry benchmark-history suite-design readiness into maturity narrative summary, sections, rendered outputs, and CLI stdout.

424-v410-project-audit-history-suite-design.md
 -> v410 code explanation: carry benchmark-history suite-design readiness into project audit context, checks, rendered outputs, and CLI stdout.

425-v411-release-bundle-history-suite-design.md
 -> v411 code explanation: carry benchmark-history suite-design readiness into release bundle context, summary, rendered outputs, and CLI stdout.

426-v412-release-gate-history-suite-design.md
 -> v412 code explanation: carry benchmark-history suite-design readiness into release gate checks, summary, rendered outputs, and CLI stdout.

427-v413-release-readiness-history-suite-design.md
 -> v413 code explanation: carry benchmark-history suite-design readiness into release readiness summary, panel status, rendered outputs, and CLI stdout.

428-v414-release-readiness-comparison-suite-design.md
 -> v414 code explanation: compare benchmark-history suite-design readiness across release readiness reports and expose deltas in artifacts and CLI stdout.

429-v415-registry-suite-design-readiness-deltas.md
 -> v415 code explanation: carry release-readiness comparison suite-design deltas into registry summaries, leaderboards, rendered outputs, and CLI stdout.

430-v416-maturity-suite-design-readiness.md
 -> v416 code explanation: carry registry suite-design readiness deltas into maturity summary, narrative, rendered outputs, and CLI stdout.

431-v417-training-portfolio-suite-design-review.md
 -> v417 code explanation: let training portfolio comparison turn maturity suite-design readiness regressions into dedicated review/blocker actions.

432-v418-training-scale-suite-design-decision-carryover.md
 -> v418 code explanation: carry suite-design regression context from batch reviews into scale-run comparison, decision, workflow, outputs, and CLI evidence.

433-v419-training-scale-handoff-suite-design-carryover.md
 -> v419 code explanation: carry suite-design regression context into training scale handoff validation, outputs, CLI diagnostics, and strict clean-batch guard checks.

434-v420-training-scale-promotion-suite-design-carryover.md
 -> v420 code explanation: carry suite-design regression context into training scale promotion acceptance, outputs, CLI diagnostics, and strict clean-batch promotion guard checks.

435-v421-training-scale-promotion-index-suite-design-carryover.md
 -> v421 code explanation: carry suite-design regression context into training scale promotion indexes, compare-input filtering, outputs, and CLI diagnostics.

436-v422-promoted-training-scale-comparison-suite-design-carryover.md
 -> v422 code explanation: carry suite-design regression context into promoted training scale comparisons, stale-index filtering, outputs, and CLI diagnostics.

437-v423-promoted-training-scale-decision-suite-design-carryover.md
 -> v423 code explanation: carry suite-design regression context into promoted training scale baseline decisions, rejected candidates, outputs, and CLI diagnostics.

438-v424-promoted-training-scale-seed-suite-design-carryover.md
 -> v424 code explanation: carry suite-design regression context into promoted training scale next-cycle seeds, outputs, recommendations, and CLI diagnostics.

439-v425-promoted-training-scale-seed-handoff-suite-design-carryover.md
 -> v425 code explanation: carry suite-design regression context into final promoted seed handoff reports, strict clean-batch gating, outputs, recommendations, and CLI diagnostics.

440-v426-promoted-seed-handoff-receipt-suite-design-contract.md
 -> v426 code explanation: upgrade promoted seed handoff automation receipts to schema v3 and validate suite-design regression fields through receipt checks, embedded checks, and handoff assurance.

441-v427-promoted-seed-handoff-receipt-contract-hardening.md
 -> v427 code explanation: harden schema-v3 suite-design receipt sidecars by checking regression names in assurance smoke evidence and rejecting tampered count/name sidecars.

442-v428-promoted-seed-handoff-receipt-contract-summary.md
 -> v428 code explanation: add a compact schema-v3 receipt contract summary over handoff assurance, sidecar status, and suite-design count/name consistency.

443-v429-promoted-seed-handoff-receipt-contract-summary-check.md
 -> v429 code explanation: add a self-check layer that rebuilds receipt contract summaries and validates JSON/text/Markdown/HTML sidecars against the source handoff.

444-v430-promoted-seed-handoff-assurance-smoke-contract-summary-check.md
 -> v430 code explanation: wire receipt contract summary generation and summary-check sidecars into the promoted seed handoff assurance smoke command.

445-v431-promoted-seed-handoff-assurance-smoke-contract-helper.md
 -> v431 code explanation: split receipt contract summary/check handling out of the assurance smoke orchestration script while preserving v430 outputs.

446-v432-baseline-candidate-eval-loop.md
 -> v432 code explanation: turn tiny scorecard comparison smoke into a reusable baseline-candidate eval loop with control checks, acceptance criteria, strict gate exits, summary reuse, and execution metadata.

447-v433-baseline-candidate-handoff.md
 -> v433 code explanation: convert a baseline-candidate eval loop report into a next-baseline handoff with checkpoint evidence, guardrail reasons, strict require-accepted exits, and compact review artifacts.

448-v434-baseline-candidate-handoff-check.md
 -> v434 code explanation: rebuild baseline-candidate handoff artifacts from their source loop report and validate next-baseline, guardrail, checkpoint, and gate metadata contracts.

449-v435-baseline-candidate-handoff-embedded-check.md
 -> v435 code explanation: embed passing handoff-check summaries and sidecar paths into baseline-candidate handoff JSON/text/Markdown/HTML without changing candidate acceptance semantics.

450-v436-baseline-candidate-threshold-matrix.md
 -> v436 code explanation: run one baseline-candidate smoke summary through multiple score-delta thresholds so accept/reject handoff paths and embedded contract checks are both covered.

451-v437-baseline-candidate-threshold-boundary.md
 -> v437 code explanation: add inclusive threshold ranges and boundary summaries that expose strictest accept, first reject, transitions, and monotonic acceptance checks.

452-v438-baseline-candidate-threshold-boundary-smoke.md
 -> v438 code explanation: run a fresh tiny scorecard comparison before rebuilding the threshold boundary matrix, proving the live pipeline passes while the candidate remains a review outcome.

453-v439-baseline-candidate-threshold-boundary-reuse-diagnosis.md
 -> v439 code explanation: let the boundary smoke reuse existing tiny summaries and emit review diagnosis issues/actions for rejected candidates.

454-v440-baseline-candidate-threshold-boundary-diagnosis-gate.md
 -> v440 code explanation: add a strict diagnosis gate that returns exit code 2 when review diagnosis is not pass while keeping exploratory runs usable.

455-v441-baseline-candidate-threshold-boundary-gate-check.md
 -> v441 code explanation: wrap the strict threshold-boundary diagnosis gate in an expected-exit contract check so intentional candidate rejection can be archived as pass evidence.

456-v442-ci-baseline-candidate-threshold-boundary-gate-check.md
 -> v442 code explanation: promote the v441 expected-exit gate check into GitHub Actions and CI workflow hygiene order checks.

457-v443-ci-baseline-candidate-threshold-boundary-wrapper-plan.md
 -> v443 code explanation: replace the long CI boundary-gate command with a stable wrapper that records invocation plan and artifact digests.

458-v444-ci-baseline-candidate-boundary-gate-plan-check.md
 -> v444 code explanation: validate the v443 CI boundary-gate wrapper plan by checking recorded artifact digests, expected-exit summary fields, and CI workflow hygiene order rules.

459-v445-ci-boundary-plan-context-carryover.md
 -> v445 code explanation: carry CI boundary gate and boundary wrapper plan-check readiness from CI workflow hygiene into project audit, release bundle, release readiness summaries, CLI output, and rendered evidence.

460-v446-release-readiness-boundary-plan-regression.md
 -> v446 code explanation: let release readiness comparison detect CI boundary gate and boundary wrapper plan-check readiness regressions even when overall release readiness remains ready.

461-v447-ci-boundary-plan-downstream-carryover.md
 -> v447 code explanation: carry release-readiness CI boundary plan-check regression counts through registry, maturity summaries, maturity narratives, and training portfolio comparison review actions.

462-v448-promoted-boundary-plan-clean-batch-carryover.md
 -> v448 code explanation: carry promoted training scale handoff CI boundary plan-check regression counts through comparison, decision, seed, handoff, receipt, embedded-check, and assurance evidence.

463-v449-promoted-receipt-v4-contract-summary.md
 -> v449 code explanation: flatten promoted seed handoff receipt schema-v4 CI boundary plan-check counts into contract summaries, summary checks, and assurance smoke output.

464-v450-promoted-receipt-contract-checks.md
 -> v450 code explanation: add machine-readable receipt contract checks for promoted seed handoff contract summaries and summary-check sidecar validation.

465-v451-promoted-receipt-summary-check-structured-comparisons.md
 -> v451 code explanation: add structured summary-field and sidecar comparisons to promoted seed handoff receipt contract summary-check outputs.

466-v452-promoted-receipt-summary-check-row-metadata.md
 -> v452 code explanation: extract receipt summary-check row helpers and add row-level metadata for field and sidecar comparisons.

467-v453-promoted-receipt-contract-check-row-metadata.md
 -> v453 code explanation: extract receipt contract check-row helpers and add row-level metadata to contract summary checks.

468-v454-promoted-receipt-contract-check-type-summary.md
 -> v454 code explanation: add status/type aggregate profiles to receipt contract checks and split contract context helpers.

469-v455-promoted-receipt-contract-profile-checks.md
 -> v455 code explanation: add summary-check consistency rows that recompute receipt contract aggregate profiles from embedded contract check rows.

470-v456-promoted-receipt-summary-check-family-summary.md
 -> v456 code explanation: add compact summary-check family rollups and failed-target rows for summary field, contract profile, and sidecar failures.

471-v457-promoted-receipt-summary-check-failure-smoke.md
 -> v457 code explanation: run controlled summary-field, contract-profile, and sidecar tamper scenarios to prove failure-family attribution.

472-v458-promoted-receipt-failure-smoke-ci-gate.md
 -> v458 code explanation: promote the receipt contract failure smoke into GitHub Actions and CI workflow hygiene order checks.

473-v459-promoted-receipt-failure-smoke-ci-wrapper.md
 -> v459 code explanation: replace the inline CI receipt failure-smoke commands with a wrapper that records command return codes and artifact digests.

474-v460-promoted-receipt-failure-smoke-plan-check.md
 -> v460 code explanation: validate the receipt failure-smoke wrapper plan through command return codes, failure-smoke summary fields, artifact digests, and CI workflow hygiene order checks.

475-v461-promoted-receipt-plan-check-carryover.md
 -> v461 code explanation: carry the receipt failure-smoke plan-check readiness field from CI hygiene into audit, release bundle, and release readiness evidence.

476-v462-release-readiness-receipt-plan-regression.md
 -> v462 code explanation: compare receipt failure-smoke plan-check readiness across release readiness reports and classify ready-to-not-ready changes as CI workflow regression reasons.

477-v463-archived-path-portability-ci-gate.md
 -> v463 code explanation: add a CI-enforced archived path portability check so Windows-authored receipt handoff sidecar paths remain resolvable on Linux runners.

478-v464-archived-path-portability-readiness-carryover.md
 -> v464 code explanation: carry archived path portability readiness from CI hygiene into audit, release bundle, and release readiness evidence.

479-v465-release-readiness-archived-path-regression.md
 -> v465 code explanation: compare archived path portability readiness across release readiness reports and classify ready-to-not-ready changes as CI workflow regression reasons.

480-v466-archived-path-maturity-portfolio-carryover.md
 -> v466 code explanation: carry archived path portability regression counts through registry, maturity summary, maturity narrative, and training portfolio review.

481-v467-promoted-training-scale-generic-ci-reason-count.md
 -> v467 code explanation: keep archived path portability regressions on the generic CI reason-count path through promoted training scale comparison and seed handoff review.

482-v468-promoted-training-scale-decision-seed-archived-reason.md
 -> v468 code explanation: carry archived path portability reason-counts through promoted training scale decision and next-cycle seed evidence.

483-v469-promoted-seed-handoff-archived-reason-gate.md
 -> v469 code explanation: carry archived path portability reason-counts through final promoted seed handoff outputs and clean-batch automation gate evidence.

484-v470-promoted-seed-handoff-receipt-ci-reason-schema-v5.md
 -> v470 code explanation: upgrade promoted seed handoff receipts to schema v5 so CI regression reason-count maps are validated through receipt checks, embedded checks, assurance, and contract summaries.

485-v471-promoted-seed-handoff-receipt-ci-reason-scope-contract.md
 -> v471 code explanation: add contract summary CI reason-count scopes and checks that selected reason maps stay within aggregate handoff reason maps.

## 一句话总览

本目录让 MiniGPT 的文档治理从“继续向一个成熟度目录堆版本”转为“阶段化同级承接”，后续训练治理文档可以继续增长而不压垮旧阶段索引。
