# MiniGPT promoted training scale next-cycle seed

- Generated: `2026-05-27T00:22:54Z`
- Seed status: `review`
- Selected baseline: `gamma`
- Decision status: `review`
- Gate: `pass`
- Batch: `completed`
- Readiness: `107`
- Sources: `1`
- Missing sources: `0`
- Baseline suite: `builtin:standard-zh`
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
- Next suite: `builtin:standard-zh`
- Next suite source: `inherited`

## Next Plan Command

```powershell
D:\python\python.exe scripts/plan_training_scale.py d\448\解释\corpus.txt --project-root D:\aiproj --out-dir d\448\解释\promoted-plan --batch-out-root d\448\解释\promoted-batch --dataset-name portfolio-zh --dataset-version-prefix v448-smoke --dataset-description "MiniGPT corpus seeded from a promoted training scale baseline." --suite-name standard-zh --sample-prompt MiniGPT --max-variants 1
```

## Sources

| Source | Exists | Kind |
| --- | --- | --- |
| d\448\解释\corpus.txt | True | file |

## Recommendations

- Review the promoted baseline decision before running the next plan command.
- If the review is accepted, reuse the generated command and keep this seed as the cycle handoff artifact.
- Rejected promoted decision inputs include handoff batch CI regressions; keep them out of the next-cycle seed baseline. Observed reasons: boundary_gate_plan_check_not_ready:1, workflow-order-regressed:1.
- Review selected handoff batch actions before treating the next-cycle seed as clean model-quality evidence.
