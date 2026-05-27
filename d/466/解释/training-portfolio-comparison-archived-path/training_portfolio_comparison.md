# MiniGPT v466 archived path portfolio comparison

- Generated: `2026-05-27T14:35:27Z`
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
| Maturity reviews | 1 |
| Maturity review portfolios | candidate |
| Maturity CI regressions | 1 |
| Maturity CI portfolios | candidate |
| Maturity CI regression reasons | archived_path_portability_check_not_ready:1 |
| Best score CI boundary plan regressions | 0 |
| Best score CI archived path regressions | 1 |
| Maturity coverage regressions | 0 |
| Maturity coverage portfolios | none |
| Maturity suite-design regressions | 0 |
| Maturity suite-design portfolios | none |
| Best score maturity | incomplete |
| Best score release readiness trend | ci-regressed |
| Best score suite-design regressions | 0 |
| Review actions | 3 |
| Blocker actions | 1 |

## Portfolios

| Portfolio | Status | Dataset | Artifacts | Score | Val Loss | Dataset | Maturity | Relation |
| --- | --- | --- | ---: | ---: | ---: | --- | --- | --- |
| baseline | completed | baseline-zh@v1 | 6/6 | 82 (+0) | 1.2 (+0) | ready | ready / stable / ci=0 / ci_order=0 / ci_boundary_plan=0 / ci_archived_paths=0 / ci_reasons=none / coverage=0 / suite=0 | Baseline portfolio. |
| candidate | completed | candidate-zh@v1 | 6/6 | 92 (+10) | 0.9 (-0.3) | ready | incomplete / ci-regressed / ci=1 / ci_order=0 / ci_boundary_plan=0 / ci_archived_paths=1 / ci_reasons=archived_path_portability_check_not_ready:1 / coverage=0 / suite=0 | overall +10; final val loss -0.3; maturity status changed; release-readiness CI regressed (archived_path_portability_check_not_ready:1) |

## Artifact Coverage

| Portfolio | Artifact | Exists | Path |
| --- | --- | --- | --- |
| baseline | run_manifest | True | D:\aiproj\d\466\解释\source-portfolios\baseline\run_manifest.json |
| baseline | eval_suite | True | D:\aiproj\d\466\解释\source-portfolios\baseline\eval_suite.json |
| baseline | generation_quality | True | D:\aiproj\d\466\解释\source-portfolios\baseline\generation_quality.json |
| baseline | benchmark_scorecard | True | D:\aiproj\d\466\解释\source-portfolios\baseline\benchmark_scorecard.json |
| baseline | dataset_card | True | D:\aiproj\d\466\解释\source-portfolios\baseline\dataset_card.json |
| baseline | registry | False |  |
| baseline | maturity_summary | False |  |
| baseline | maturity_narrative | True | D:\aiproj\d\466\解释\source-portfolios\baseline\maturity_narrative.json |
| candidate | run_manifest | True | D:\aiproj\d\466\解释\source-portfolios\candidate\run_manifest.json |
| candidate | eval_suite | True | D:\aiproj\d\466\解释\source-portfolios\candidate\eval_suite.json |
| candidate | generation_quality | True | D:\aiproj\d\466\解释\source-portfolios\candidate\generation_quality.json |
| candidate | benchmark_scorecard | True | D:\aiproj\d\466\解释\source-portfolios\candidate\benchmark_scorecard.json |
| candidate | dataset_card | True | D:\aiproj\d\466\解释\source-portfolios\candidate\dataset_card.json |
| candidate | registry | False |  |
| candidate | maturity_summary | False |  |
| candidate | maturity_narrative | True | D:\aiproj\d\466\解释\maturity-narrative-archived-path\maturity_narrative.json |

## Review Actions

| ID | Portfolio | Severity | Category | Reason | Action |
| --- | --- | --- | --- | --- | --- |
| artifact-1 | baseline | review | artifact | artifact_coverage_gap | Restore missing core artifacts before treating the comparison as a complete handoff. |
| artifact-2 | candidate | review | artifact | artifact_coverage_gap | Restore missing core artifacts before treating the comparison as a complete handoff. |
| maturity-3 | candidate | blocker | maturity | best_score_ci_regressed | Explain or fix release-readiness CI workflow regressions before promoting this best-scoring portfolio (archived_path_portability_check_not_ready:1). |

## Recommendations

- Review the best-scoring portfolio's maturity narrative before promoting it as a clean baseline.
- Block best-score promotion until release-readiness CI workflow regressions are explained or fixed (archived_path_portability_check_not_ready:1).
