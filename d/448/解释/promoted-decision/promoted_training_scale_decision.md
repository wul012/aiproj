# MiniGPT promoted training scale baseline decision

- Generated: `2026-05-27T00:22:24Z`
- Decision status: `review`
- Selected baseline: `gamma`
- Gate: `pass`
- Batch: `completed`
- Readiness: `107`
- Selected suite: `builtin:standard-zh`
- Require suite consistency: `False`
- Selected handoff suite: `consistent`
- Selected handoff mismatches: `0`
- Selected handoff suite path: `builtin:standard-zh`
- Selected handoff require clean batch review: `False`
- Selected handoff clean batch review: `None`
- Selected handoff batch CI regressions: `0`
- Selected handoff batch CI regression reasons: `none`
- Selected handoff batch CI boundary plan-check regressions: `0`
- Selected handoff batch suite-design regressions: `0`
- Selected handoff batch suite-design names: ``
- Selected handoff selected batch CI regressions: `0`
- Selected handoff selected batch CI regression reasons: `none`
- Selected handoff selected batch CI boundary plan-check regressions: `0`
- Selected handoff selected batch suite-design regressions: `0`
- Selected handoff selected batch suite-design names: ``
- Selected comparison exclusion reasons: ``
- Handoff require clean batch review: `2`
- Handoff clean batch review: `1`
- Handoff unclean batch review: `1`
- Handoff batch CI regressions: `2`
- Handoff batch CI regression reasons: `boundary_gate_plan_check_not_ready:1, workflow-order-regressed:1`
- Handoff batch CI boundary plan-check regressions: `1`
- Handoff selected batch CI regressions: `1`
- Handoff selected batch CI regression reasons: `boundary_gate_plan_check_not_ready:1`
- Handoff selected batch CI boundary plan-check regressions: `1`
- Handoff batch CI-regressed names: `beta-boundary-plan`
- Handoff batch suite-design regressions: `0`
- Handoff selected batch suite-design regressions: `0`
- Handoff batch suite-design names: ``
- Handoff selected batch suite-design names: ``
- Comparison exclusion reasons: `handoff batch CI regression count is 2`
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
- Comparison-ready selected batch suite-design regressions: `0`
- Comparison-ready handoff batch suite-design names: ``
- Comparison-ready selected batch suite-design names: ``
- Selected handoff batch review: `review`
- Selected handoff batch review actions: `2`
- Selected handoff batch blocker actions: `0`
- Comparison-ready handoff batch reviews: `1`
- Comparison-ready handoff batch blockers: `1`
- Comparison-ready handoff batch blocker reasons: `coverage-regressed`
- Handoff suite consistent: `3`
- Handoff suite mismatches: `0`
- Candidates: `2`
- Rejected: `1`
- Comparison status: `compared`
- Suite consistency: `consistent`

## Rejected Runs

| Run | Gate | Batch | Score | Reasons |
| --- | --- | --- | ---: | --- |
| beta-boundary-plan |  |  |  | run was not promoted for comparison; handoff batch CI regression count is 2; batch did not complete; readiness_score below 60 |

## Recommendations

- Review the remaining promoted runs before turning this baseline into the next run seed.
- Gate warnings can be accepted for review, but they should be justified before larger training.
- Rejected promoted inputs include handoff batch CI regressions caused by boundary plan-check readiness; keep them out of baseline selection until the CI boundary evidence is clean. Observed reasons: boundary_gate_plan_check_not_ready:1, workflow-order-regressed:1.
- Review selected handoff batch actions before using this baseline as clean model-quality evidence.
