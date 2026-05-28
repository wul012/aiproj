# MiniGPT promoted training scale next-cycle seed

- Generated: `2026-05-28T03:58:02Z`
- Seed status: `ready`
- Selected baseline: `beta`
- Decision status: `accepted`
- Gate: `pass`
- Batch: `completed`
- Readiness: `107`
- Sources: `1`
- Missing sources: `0`
- Baseline suite: `None`
- Selected handoff suite: `consistent`
- Selected handoff mismatches: `0`
- Selected handoff suite path: `builtin:standard-zh`
- Selected handoff require clean batch review: `True`
- Selected handoff clean batch review: `clean`
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
- Handoff require clean batch review: `3`
- Handoff clean batch review: `2`
- Handoff unclean batch review: `1`
- Handoff batch CI regressions: `3`
- Handoff batch CI regression reasons: `archived_path_portability_check_not_ready:1, missing-ci-step:1, workflow-order-regressed:1`
- Handoff batch CI boundary plan-check regressions: `1`
- Handoff selected batch CI regressions: `2`
- Handoff selected batch CI regression reasons: `archived_path_portability_check_not_ready:1, workflow-order-regressed:1`
- Handoff selected batch CI boundary plan-check regressions: `1`
- Handoff batch CI-regressed names: `dirty-ci-old`
- Handoff batch suite-design regressions: `None`
- Handoff selected batch suite-design regressions: `None`
- Handoff batch suite-design names: ``
- Handoff selected batch suite-design names: ``
- Comparison exclusion reasons: `handoff batch CI regression count is 3`
- Comparison-ready clean-required handoffs: `2`
- Comparison-ready clean handoffs: `2`
- Comparison-ready unclean handoffs: `0`
- Comparison-ready handoff batch CI regressions: `0`
- Comparison-ready handoff batch CI regression reasons: `none`
- Comparison-ready handoff batch CI boundary plan-check regressions: `0`
- Comparison-ready selected batch CI regressions: `0`
- Comparison-ready selected batch CI regression reasons: `none`
- Comparison-ready selected batch CI boundary plan-check regressions: `0`
- Comparison-ready handoff batch CI-regressed names: ``
- Comparison-ready handoff batch suite-design regressions: `None`
- Comparison-ready selected batch suite-design regressions: `None`
- Comparison-ready handoff batch suite-design names: ``
- Comparison-ready selected batch suite-design names: ``
- Selected handoff batch review: `blocker`
- Selected handoff batch review actions: `2`
- Selected handoff batch blocker actions: `1`
- Comparison-ready handoff batch reviews: `1`
- Comparison-ready handoff batch blockers: `1`
- Comparison-ready handoff batch blocker reasons: `coverage-regressed`
- Handoff suite consistent: `2`
- Handoff suite mismatches: `0`
- Next suite: `data\eval_prompts.json`
- Next suite source: `default`

## Next Plan Command

```powershell
D:\python\python.exe scripts/plan_training_scale.py d\468\解释\seed-source\corpus.txt --project-root . --out-dir d\468\解释\promoted-training-scale-seed-plan --batch-out-root d\468\解释\promoted-training-scale-seed-batch --dataset-name portfolio-zh --dataset-version-prefix v468 --dataset-description "MiniGPT corpus seeded from a promoted training scale baseline." --sample-prompt MiniGPT --max-variants 3
```

## Sources

| Source | Exists | Kind |
| --- | --- | --- |
| d\468\解释\seed-source\corpus.txt | True | file |

## Recommendations

- Run the generated plan command on the next corpus, then pass its outputs through the v70-v80 training scale chain.
- Keep the selected promoted baseline path in the seed report so the next cycle can explain where it came from.
- Rejected promoted decision inputs include handoff batch CI regressions; keep them out of the next-cycle seed baseline. Observed reasons: archived_path_portability_check_not_ready:1, missing-ci-step:1, workflow-order-regressed:1.
- Resolve selected handoff batch blocker actions before treating the next-cycle seed as clean model-quality evidence.
