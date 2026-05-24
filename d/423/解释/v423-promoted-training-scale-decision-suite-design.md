# MiniGPT promoted training scale baseline decision

- Generated: `2026-05-24T07:35:28Z`
- Decision status: `review`
- Selected baseline: `beta`
- Gate: `pass`
- Batch: `completed`
- Readiness: `107`
- Selected suite: `builtin:standard-zh`
- Require suite consistency: `False`
- Selected handoff suite: `consistent`
- Selected handoff mismatches: `0`
- Selected handoff suite path: `builtin:standard-zh`
- Selected handoff require clean batch review: `True`
- Selected handoff clean batch review: `clean`
- Selected handoff batch CI regressions: `0`
- Selected handoff batch CI regression reasons: `none`
- Selected handoff batch suite-design regressions: `0`
- Selected handoff batch suite-design names: ``
- Selected handoff selected batch CI regressions: `0`
- Selected handoff selected batch CI regression reasons: `none`
- Selected handoff selected batch suite-design regressions: `0`
- Selected handoff selected batch suite-design names: ``
- Selected comparison exclusion reasons: ``
- Handoff require clean batch review: `3`
- Handoff clean batch review: `2`
- Handoff unclean batch review: `1`
- Handoff batch CI regressions: `0`
- Handoff batch CI regression reasons: `none`
- Handoff selected batch CI regressions: `0`
- Handoff selected batch CI regression reasons: `none`
- Handoff batch CI-regressed names: ``
- Handoff batch suite-design regressions: `2`
- Handoff selected batch suite-design regressions: `1`
- Handoff batch suite-design names: `beta-suite, standard`
- Handoff selected batch suite-design names: `beta-suite`
- Comparison exclusion reasons: `handoff batch suite-design regression count is 2`
- Comparison-ready clean-required handoffs: `2`
- Comparison-ready clean handoffs: `2`
- Comparison-ready unclean handoffs: `0`
- Comparison-ready handoff batch CI regressions: `0`
- Comparison-ready handoff batch CI regression reasons: `none`
- Comparison-ready selected batch CI regressions: `0`
- Comparison-ready selected batch CI regression reasons: `none`
- Comparison-ready handoff batch CI-regressed names: ``
- Comparison-ready handoff batch suite-design regressions: `0`
- Comparison-ready selected batch suite-design regressions: `0`
- Comparison-ready handoff batch suite-design names: ``
- Comparison-ready selected batch suite-design names: ``
- Selected handoff batch review: `None`
- Selected handoff batch review actions: `None`
- Selected handoff batch blocker actions: `None`
- Comparison-ready handoff batch reviews: `0`
- Comparison-ready handoff batch blockers: `0`
- Comparison-ready handoff batch blocker reasons: ``
- Handoff suite consistent: `3`
- Handoff suite mismatches: `0`
- Candidates: `2`
- Rejected: `1`
- Comparison status: `compared`
- Suite consistency: `consistent`

## Rejected Runs

| Run | Gate | Batch | Score | Reasons |
| --- | --- | --- | ---: | --- |
| dirty-suite | pass | completed | 95 | run was not promoted for comparison; handoff batch suite-design regression count is 2 |

## Recommendations

- Review the remaining promoted runs before turning this baseline into the next run seed.
- Gate warnings can be accepted for review, but they should be justified before larger training.
- Rejected promoted inputs include handoff batch suite-design regressions; keep them out of baseline selection until suite-design evidence is clean. Observed names: beta-suite, standard.
