# MiniGPT promoted training scale comparison

- Generated: `2026-05-28T02:38:49Z`
- Comparison status: `compared`
- Promoted inputs: `3`
- Compare-ready inputs: `2`
- Compared runs: `2`
- Baseline: `alpha`
- Suite consistency: `consistent`
- Handoff strict suite: `3`
- Handoff suite consistent: `3`
- Handoff suite mismatches: `0`
- Handoff require clean batch review: `2`
- Handoff clean batch review: `1`
- Handoff unclean batch review: `1`
- Handoff batch CI regressions: `3`
- Handoff batch CI regression reasons: `archived_path_portability_check_not_ready:1, missing-ci-step:1, workflow-order-regressed:1`
- Handoff batch CI boundary plan-check regressions: `1`
- Handoff selected batch CI regressions: `2`
- Handoff selected batch CI regression reasons: `archived_path_portability_check_not_ready:1, workflow-order-regressed:1`
- Handoff selected batch CI boundary plan-check regressions: `1`
- Handoff batch CI-regressed names: `beta-old-ci`
- Handoff batch suite-design regressions: `0`
- Handoff batch suite-design names: ``
- Handoff selected batch suite-design regressions: `0`
- Handoff selected batch suite-design names: ``
- Comparison-ready handoff suite mismatches: `0`
- Comparison-ready clean-required handoffs: `1`
- Comparison-ready clean handoffs: `1`
- Comparison-ready unclean handoffs: `0`
- Comparison-ready handoff batch CI regressions: `0`
- Comparison-ready handoff batch CI regression reasons: `none`
- Comparison-ready handoff batch CI boundary plan-check regressions: `0`
- Comparison-ready selected batch CI regressions: `0`
- Comparison-ready selected batch CI regression reasons: `none`
- Comparison-ready selected batch CI boundary plan-check regressions: `0`
- Comparison-ready handoff batch CI-regressed names: ``
- Comparison-ready handoff batch suite-design regressions: `0`
- Comparison-ready handoff batch suite-design names: ``
- Comparison-ready selected batch suite-design regressions: `0`
- Comparison-ready selected batch suite-design names: ``
- Comparison-ready selected batch reviews: `1`
- Comparison-ready selected batch blockers: `1`
- Comparison-ready batch review actions: `4`
- Comparison-ready batch blocker actions: `1`

## Promoted Inputs

| Name | Status | Compare | Readiness | Handoff Suite | Mismatches | Clean Required | Clean Status | CI Regressions | Suite-Design Regressions | Exclusion | Selected Suite | Batch Review | Batch Blockers | Run |
| --- | --- | --- | ---: | --- | ---: | --- | --- | ---: | ---: | --- | --- | --- | ---: | --- |
| alpha | promoted | True | 90 | consistent | 0 | True | clean |  |  |  | builtin:standard-zh | blocker | 1 | d\467\解释\source-index\promotion-index\..\runs\alpha\training_scale_run.json |
| beta | promoted | False |  | consistent | 0 | True | clean | 3 |  | handoff batch CI regression count is 3 | builtin:standard-zh | review | 0 | d\467\解释\source-index\promotion-index\..\runs\beta\training_scale_run.json |
| gamma | promoted | True | 107 | consistent | 0 | False |  |  |  |  | builtin:standard-zh | review | 0 | d\467\解释\source-index\promotion-index\..\runs\gamma\training_scale_run.json |

## Comparison

- Compared runs: `2`
- Allowed: `2`
- Blocked: `0`
- Suite consistency: `consistent`
- Best by readiness: `gamma`

| Run | Status | Allowed | Gate | Batch | Suite | Score | Relation |
| --- | --- | --- | --- | --- | --- | ---: | --- |
| alpha | completed | True | warn | completed | builtin:standard-zh | 90 | baseline |
| gamma | completed | True | pass | completed | builtin:standard-zh | 107 | readiness +17; gate improved |

## Recommendations

- Use the compared promoted runs as the baseline for the next training-scale decision.
- Keep review and blocked promotions in the index, but do not feed them into comparison runs.
- Comparison-ready promoted inputs still carry selected handoff batch blocker actions; resolve them before treating this comparison as clean model-quality evidence.
- CI-regressed handoff batch evidence remains visible in the promotion list but is kept out of clean-required promoted comparisons. Observed reasons: archived_path_portability_check_not_ready:1, missing-ci-step:1, workflow-order-regressed:1.
- Comparison-ready batch blocker reasons: coverage-regressed
