# MiniGPT promoted training scale next-cycle seed

- Generated: `2026-05-24T00:00:00Z`
- Seed status: `ready`
- Selected baseline: `beta`
- Decision status: `accepted`
- Gate: `pass`
- Batch: `completed`
- Readiness: `107`
- Sources: `1`
- Missing sources: `0`
- Baseline suite: `builtin:standard-zh`
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
- Handoff batch CI regressions: `None`
- Handoff batch CI regression reasons: `none`
- Handoff selected batch CI regressions: `None`
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
- Comparison-ready handoff batch CI regressions: `None`
- Comparison-ready handoff batch CI regression reasons: `none`
- Comparison-ready selected batch CI regressions: `None`
- Comparison-ready selected batch CI regression reasons: `none`
- Comparison-ready handoff batch CI-regressed names: ``
- Comparison-ready handoff batch suite-design regressions: `0`
- Comparison-ready selected batch suite-design regressions: `0`
- Comparison-ready handoff batch suite-design names: ``
- Comparison-ready selected batch suite-design names: ``
- Selected handoff batch review: `None`
- Selected handoff batch review actions: `None`
- Selected handoff batch blocker actions: `None`
- Comparison-ready handoff batch reviews: `None`
- Comparison-ready handoff batch blockers: `None`
- Comparison-ready handoff batch blocker reasons: ``
- Handoff suite consistent: `2`
- Handoff suite mismatches: `0`
- Next suite: `builtin:standard-zh`
- Next suite source: `inherited`

## Next Plan Command

```powershell
python scripts/plan_training_scale.py D:\aiproj\d\424\解释\evidence-input\corpus.txt --project-root D:\aiproj\d\424\解释\evidence-input --out-dir D:\aiproj\d\424\解释\evidence-input\plan --batch-out-root D:\aiproj\d\424\解释\evidence-input\batch --dataset-name portfolio-zh --dataset-version-prefix v424-evidence --dataset-description "MiniGPT corpus seeded from a promoted training scale baseline." --suite-name standard-zh --sample-prompt MiniGPT --max-variants 3
```

## Sources

| Source | Exists | Kind |
| --- | --- | --- |
| D:\aiproj\d\424\解释\evidence-input\corpus.txt | True | file |

## Recommendations

- Run the generated plan command on the next corpus, then pass its outputs through the v70-v80 training scale chain.
- Keep the selected promoted baseline path in the seed report so the next cycle can explain where it came from.
- Rejected promoted decision inputs include handoff batch suite-design regressions; keep them out of the next-cycle seed baseline. Observed names: beta-suite, standard.
