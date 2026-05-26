# MiniGPT training portfolio comparison

- Generated: `2026-05-26T13:42:51Z`
- Portfolios: `2`
- Baseline: `baseline`
- Best overall score: `candidate`
- Best final validation loss: `candidate`

## Summary

| Field | Value |
| --- | --- |
| Completed | 2 |
| Failed | 0 |
| Planned | 0 |
| Score improvements | 1 |
| Score regressions | 0 |
| Artifact regressions | 0 |
| Dataset warnings | 0 |
| Maturity reviews | 0 |
| Maturity review portfolios | none |
| Maturity CI regressions | 1 |
| Maturity CI portfolios | candidate |
| Maturity CI regression reasons | boundary_gate_plan_check_not_ready:1 |
| Best score CI boundary plan regressions | 1 |
| Maturity coverage regressions | 0 |
| Maturity coverage portfolios | none |
| Maturity suite-design regressions | 0 |
| Maturity suite-design portfolios | none |
| Best score maturity | ready |
| Best score release readiness trend | ci-regressed |
| Best score suite-design regressions | 0 |
| Review actions | 1 |
| Blocker actions | 1 |

## Portfolios

| Portfolio | Status | Dataset | Artifacts | Score | Val Loss | Dataset | Maturity | Relation |
| --- | --- | --- | ---: | ---: | ---: | --- | --- | --- |
| baseline | completed | baseline-dataset@v1 | 8/8 | 82 (+0) | 1.2 (+0) | ready | ready / stable / ci=0 / ci_order=0 / ci_boundary_plan=0 / ci_reasons=none / coverage=0 / suite=0 | Baseline portfolio. |
| candidate | completed | candidate-dataset@v1 | 8/8 | 91 (+9) | 0.9 (-0.3) | ready | ready / ci-regressed / ci=1 / ci_order=0 / ci_boundary_plan=1 / ci_reasons=boundary_gate_plan_check_not_ready:1 / coverage=0 / suite=0 | overall +9; final val loss -0.3; release-readiness CI regressed (boundary_gate_plan_check_not_ready:1) |

## Artifact Coverage

| Portfolio | Artifact | Exists | Path |
| --- | --- | --- | --- |
| baseline | run_manifest | True | D:\aiproj\d\447\解释\portfolio-fixture\baseline\run\run_manifest.json |
| baseline | eval_suite | True | D:\aiproj\d\447\解释\portfolio-fixture\baseline\run\eval_suite\eval_suite.json |
| baseline | generation_quality | True | D:\aiproj\d\447\解释\portfolio-fixture\baseline\run\eval_suite\generation-quality\generation_quality.json |
| baseline | benchmark_scorecard | True | D:\aiproj\d\447\解释\portfolio-fixture\baseline\run\benchmark-scorecard\benchmark_scorecard.json |
| baseline | dataset_card | True | D:\aiproj\d\447\解释\portfolio-fixture\baseline\dataset\dataset_card.json |
| baseline | registry | True | D:\aiproj\d\447\解释\portfolio-fixture\baseline\registry\registry.json |
| baseline | maturity_summary | True | D:\aiproj\d\447\解释\portfolio-fixture\baseline\maturity-summary\maturity_summary.json |
| baseline | maturity_narrative | True | D:\aiproj\d\447\解释\portfolio-fixture\baseline\maturity-narrative\maturity_narrative.json |
| candidate | run_manifest | True | D:\aiproj\d\447\解释\portfolio-fixture\candidate\run\run_manifest.json |
| candidate | eval_suite | True | D:\aiproj\d\447\解释\portfolio-fixture\candidate\run\eval_suite\eval_suite.json |
| candidate | generation_quality | True | D:\aiproj\d\447\解释\portfolio-fixture\candidate\run\eval_suite\generation-quality\generation_quality.json |
| candidate | benchmark_scorecard | True | D:\aiproj\d\447\解释\portfolio-fixture\candidate\run\benchmark-scorecard\benchmark_scorecard.json |
| candidate | dataset_card | True | D:\aiproj\d\447\解释\portfolio-fixture\candidate\dataset\dataset_card.json |
| candidate | registry | True | D:\aiproj\d\447\解释\portfolio-fixture\candidate\registry\registry.json |
| candidate | maturity_summary | True | D:\aiproj\d\447\解释\portfolio-fixture\candidate\maturity-summary\maturity_summary.json |
| candidate | maturity_narrative | True | D:\aiproj\d\447\解释\portfolio-fixture\candidate\maturity-narrative\maturity_narrative.json |

## Review Actions

| ID | Portfolio | Severity | Category | Reason | Action |
| --- | --- | --- | --- | --- | --- |
| maturity-1 | candidate | blocker | maturity | best_score_ci_regressed | Explain or fix release-readiness CI workflow regressions before promoting this best-scoring portfolio (boundary_gate_plan_check_not_ready:1). |

## Recommendations

- Block best-score promotion until release-readiness CI workflow regressions are explained or fixed (boundary_gate_plan_check_not_ready:1).
