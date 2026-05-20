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

## 一句话总览

本目录让 MiniGPT 的文档治理从“继续向一个成熟度目录堆版本”转为“阶段化同级承接”，后续训练治理文档可以继续增长而不压垮旧阶段索引。
