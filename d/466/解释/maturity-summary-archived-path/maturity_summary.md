# MiniGPT v466 archived path maturity carryover

- Generated: `2026-05-27T14:33:43Z`
- Project root: `.`

## Overview

| Key | Value |
| --- | --- |
| Current version | 465 |
| Published versions | 410 |
| Archive versions | 301 |
| Explanation versions | 463 |
| Average maturity level | 4.5 |
| Overall status | warn |
| Registry runs | 1 |
| Release readiness trend | ci-regressed |
| Release readiness deltas | 1 |
| Release readiness regressions | 0 |
| Release readiness CI workflow regressions | 1 |
| Release readiness CI order regressions | 0 |
| Release readiness CI regression reasons | archived_path_portability_check_not_ready:1 |
| Release readiness CI tiny plan regressions | 0 |
| Release readiness CI boundary gate regressions | 0 |
| Release readiness CI boundary plan regressions | 0 |
| Release readiness CI archived path regressions | 1 |
| Release readiness CI drift smoke regressions | 0 |
| Release readiness test coverage regressions | 0 |
| Release readiness benchmark-history regressions | 0 |
| Release readiness benchmark suite-design deltas | 0 |
| Release readiness benchmark suite-design regressions | 0 |
| Release readiness benchmark design changes | 0 |
| Release readiness benchmark requirement changes | 0 |
| Release readiness benchmark requirement exit delta | 0 |
| Release readiness benchmark failed reasons added | 0 |
| Release readiness benchmark failed reasons removed | 0 |
| Release readiness benchmark failed reason removals | none |
| Release readiness benchmark failed reason recovery deltas | 0 |
| Release readiness benchmark failed reason mixed deltas | 0 |
| Release readiness benchmark failed reason drift | stable:1 |
| Release readiness max benchmark suite-design delta | 0 |
| Release readiness max benchmark design-change delta | 0 |
| Request history status |  |
| Request history records |  |

## Capability Matrix

| Area | Status | Level | Score | Evidence | Next step |
| --- | --- | ---: | ---: | --- | --- |
| Model Core | pass | 4/4 | 100.0% | Tokenizer, GPT blocks, training artifacts, BPE, attention, prediction, chat wrapper, model reports, and sampling controls. | Train larger baselines and compare scale/quality changes on fixed benchmark prompts. |
| Data And Reproducibility | pass | 4/4 | 100.0% | Dataset preparation, run manifests, dataset quality checks, eval suites, benchmark metadata, and dataset version manifests. | Add dataset cards and stable train/validation/test split policies for larger corpora. |
| Evaluation Benchmarks | pass | 4/4 | 100.0% | Fixed prompt eval, generation quality, baseline comparison, pair batch, pair trend, dashboard links, registry links, and delta leaders. | Consolidate eval and pair outputs into one benchmark suite with task-level pass/fail scoring. |
| Local Inference And Playground | pass | 5/5 | 100.0% | Static playground, local API, safety profiles, checkpoint selector, checkpoint comparison, side-by-side generation, saved pair artifacts, streaming, request history, row detail JSON, and request history summaries. | Connect request history stability summaries to audit/release handoff when local serving evidence becomes release-relevant. |
| Registry And Reporting | pass | 5/5 | 100.0% | Dashboard, run comparison, registry HTML, saved views, annotations, leaderboards, experiment/model cards, pair report registry views, and release readiness trend tracking. | Feed release readiness trend context into maturity review and release summaries. |
| Release Governance | pass | 5/5 | 100.0% | Project audit, release bundle, release gate, generation quality policy, policy profiles, profile comparison, deltas, configurable baselines, request-history audit gates, readiness dashboard, and readiness comparison. | Use release readiness trend context to guide maturity and release review instead of adding more gate variants. |
| Documentation And Evidence | pass | 5/5 | 100.0% | Version tags, README history, code explanations, archived screenshots, browser checks, maturity summary, and release trend evidence. | Keep future code explanations tied to concrete evidence and summarize phases instead of expanding every small link change. |
| Project Synthesis | pass | 4/4 | 100.0% | Experiment cards, model cards, audit/bundle/gate outputs, baseline comparison, request-history context, release readiness context, registry trend tracking, and maturity summary. | Use maturity trend context to choose the next real capability: larger data, benchmark hardening, or serving review. |

## Phase Timeline

| Versions | Phase | Status |
| --- | --- | --- |
| v1-v12 | MiniGPT learning core | pass |
| v13-v24 | Data, registry, and cards | pass |
| v25-v34 | Release governance | pass |
| v35-v47 | Evaluation benchmark and pair reports | pass |
| v48-v60 | Project maturity and local inference hardening | pass |
| v61-v65 | Release readiness and maturity trend context | pass |

## Request History Context

| Key | Value |
| --- | --- |
| Available | False |
| Status |  |
| Records |  |
| Invalid |  |
| Timeout rate |  |
| Bad request rate |  |
| Error rate |  |
| Checkpoints |  |
| Latest |  |

## Release Readiness Trend Context

| Key | Value |
| --- | --- |
| Available | True |
| Trend status | ci-regressed |
| Comparison counts | ci-regressed:1 |
| Delta count | 1 |
| Runs with deltas | 1 |
| Regressed | 0 |
| Improved | 0 |
| Panel changed | 0 |
| Changed panels | 0 |
| Max status delta | 0 |
| CI workflow regressions | 1 |
| CI workflow order regressions | 0 |
| CI workflow status changes | 0 |
| CI workflow regression reasons | archived_path_portability_check_not_ready:1 |
| CI tiny plan regressions | 0 |
| CI boundary gate regressions | 0 |
| CI boundary plan regressions | 0 |
| CI archived path regressions | 1 |
| CI drift smoke regressions | 0 |
| Max CI workflow failed-check delta | 0 |
| Max CI workflow order-violation delta | 0 |
| Test coverage regressions | 0 |
| Test coverage status changes | 0 |
| Max coverage percent delta | 0 |
| Max coverage gap delta | 0 |
| Benchmark-history regressions | 0 |
| Benchmark suite-design deltas | 0 |
| Benchmark suite-design regressions | 0 |
| Benchmark design changes | 0 |
| Benchmark-history status changes | 0 |
| Benchmark-history boundary changes | 0 |
| Benchmark requirement changes | 0 |
| Benchmark requirement exit delta | 0 |
| Benchmark failed reasons added | 0 |
| Benchmark failed reasons removed | 0 |
| Benchmark failed reason removals | none |
| Benchmark failed reason recovery deltas | 0 |
| Benchmark failed reason mixed deltas | 0 |
| Benchmark failed reason drift | stable:1 |
| Max benchmark case-regression delta | 0 |
| Max benchmark generation-flag regression delta | 0 |
| Max benchmark suite-design delta | 0 |
| Max benchmark design-change delta | 0 |

## Recommendations

- Treat v48 as a phase summary: avoid continuing to split links/trends/dashboard unless the change improves evaluation quality.
- Next high-value step: consolidate eval suite, generation quality, pair batch, and pair delta leaders into one benchmark scoring suite.
- Use the maturity matrix to explain the project as a learning AI engineering artifact, not as a production-grade model service.
- Review CI workflow hygiene regressions (archived_path_portability_check_not_ready:1) before presenting the project as release-stable; maturity status is downgraded to review.
- Generate request_history_summary.json before local serving review so maturity context includes recent inference stability.
