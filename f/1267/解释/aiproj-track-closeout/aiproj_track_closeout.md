# MiniGPT aiproj Production-Excellence Closeout

- Generated: `2026-07-07T06:57:06Z`
- Status: `pass`
- Decision: `aiproj_track_closeout_ready`
- Final evidence: `docs/aiproj-track-final-evidence.md`

## Summary

| Metric | Value |
| --- | --- |
| evidence_doc_count | 6 |
| check_count | 57 |
| passed_check_count | 57 |
| failed_check_count | 0 |
| no_promotion_boundary_ready | True |
| final_evidence_ready | True |
| ci_closeout_gate_ready | True |

## Checks

| ID | Target | Expected | Actual | Status |
| --- | --- | --- | --- | --- |
| evidence_doc_exists:A0 | docs/aiproj-track-a0-census.md | file exists | present | pass |
| evidence_doc_term:A0:archive + `runs/` inventory | docs/aiproj-track-a0-census.md | archive + `runs/` inventory | present | pass |
| evidence_doc_term:A0:f/1260 | docs/aiproj-track-a0-census.md | f/1260 | present | pass |
| evidence_doc_term:A0:no training | docs/aiproj-track-a0-census.md | no training | present | pass |
| evidence_doc_exists:A1 | docs/aiproj-track-a1-static-analysis.md | file exists | present | pass |
| evidence_doc_term:A1:scripts/check_static_analysis.py | docs/aiproj-track-a1-static-analysis.md | scripts/check_static_analysis.py | present | pass |
| evidence_doc_term:A1:scripts/check_type_analysis.py | docs/aiproj-track-a1-static-analysis.md | scripts/check_type_analysis.py | present | pass |
| evidence_doc_term:A1:f/1261 | docs/aiproj-track-a1-static-analysis.md | f/1261 | present | pass |
| evidence_doc_term:A1:f/1262 | docs/aiproj-track-a1-static-analysis.md | f/1262 | present | pass |
| evidence_doc_exists:A2 | docs/aiproj-track-a2-coverage.md | file exists | present | pass |
| evidence_doc_term:A2:fail_under = 88.98 | docs/aiproj-track-a2-coverage.md | fail_under = 88.98 | present | pass |
| evidence_doc_term:A2:scripts/run_test_coverage.py | docs/aiproj-track-a2-coverage.md | scripts/run_test_coverage.py | present | pass |
| evidence_doc_term:A2:coverage-floor.json | docs/aiproj-track-a2-coverage.md | coverage-floor.json | present | pass |
| evidence_doc_exists:A3-honest-measurement | docs/aiproj-track-a3-honest-measurement.md | file exists | present | pass |
| evidence_doc_term:A3-honest-measurement:scripts/check_model_capability_honest_measurement.py | docs/aiproj-track-a3-honest-measurement.md | scripts/check_model_capability_honest_measurement.py | present | pass |
| evidence_doc_term:A3-honest-measurement:no-promotion | docs/aiproj-track-a3-honest-measurement.md | no-promotion | present | pass |
| evidence_doc_term:A3-honest-measurement:tests/ | docs/aiproj-track-a3-honest-measurement.md | tests/ | present | pass |
| evidence_doc_exists:A3-artifact-schema | docs/aiproj-track-a3-artifact-schema-guard.md | file exists | present | pass |
| evidence_doc_term:A3-artifact-schema:scripts/check_artifact_schema_guard.py | docs/aiproj-track-a3-artifact-schema-guard.md | scripts/check_artifact_schema_guard.py | present | pass |
| evidence_doc_term:A3-artifact-schema:docs/artifact-schema-guard-registry.json | docs/aiproj-track-a3-artifact-schema-guard.md | docs/artifact-schema-guard-registry.json | present | pass |
| evidence_doc_term:A3-artifact-schema:f/1265 | docs/aiproj-track-a3-artifact-schema-guard.md | f/1265 | present | pass |
| evidence_doc_exists:A4 | docs/aiproj-track-a4-code-health.md | file exists | present | pass |
| evidence_doc_term:A4:scripts/check_file_size_ratchet.py | docs/aiproj-track-a4-code-health.md | scripts/check_file_size_ratchet.py | present | pass |
| evidence_doc_term:A4:docs/code-health/file-size-ratchet.json | docs/aiproj-track-a4-code-health.md | docs/code-health/file-size-ratchet.json | present | pass |
| evidence_doc_term:A4:waiver | docs/aiproj-track-a4-code-health.md | waiver | present | pass |
| final_evidence:exists | docs/aiproj-track-final-evidence.md | file exists | present | pass |
| final_evidence:term:A0 | docs/aiproj-track-final-evidence.md | A0 | present | pass |
| final_evidence:term:A1 | docs/aiproj-track-final-evidence.md | A1 | present | pass |
| final_evidence:term:A2 | docs/aiproj-track-final-evidence.md | A2 | present | pass |
| final_evidence:term:A3 | docs/aiproj-track-final-evidence.md | A3 | present | pass |
| final_evidence:term:A4 | docs/aiproj-track-final-evidence.md | A4 | present | pass |
| final_evidence:term:A5 | docs/aiproj-track-final-evidence.md | A5 | present | pass |
| final_evidence:term:docs/aiproj-track-a0-census.md | docs/aiproj-track-final-evidence.md | docs/aiproj-track-a0-census.md | present | pass |
| final_evidence:term:docs/aiproj-track-a1-static-analysis.md | docs/aiproj-track-final-evidence.md | docs/aiproj-track-a1-static-analysis.md | present | pass |
| final_evidence:term:docs/aiproj-track-a2-coverage.md | docs/aiproj-track-final-evidence.md | docs/aiproj-track-a2-coverage.md | present | pass |
| final_evidence:term:docs/aiproj-track-a3-honest-measurement.md | docs/aiproj-track-final-evidence.md | docs/aiproj-track-a3-honest-measurement.md | present | pass |
| final_evidence:term:docs/aiproj-track-a3-artifact-schema-guard.md | docs/aiproj-track-final-evidence.md | docs/aiproj-track-a3-artifact-schema-guard.md | present | pass |
| final_evidence:term:docs/aiproj-track-a4-code-health.md | docs/aiproj-track-final-evidence.md | docs/aiproj-track-a4-code-health.md | present | pass |
| final_evidence:term:docs/no-promotion-boundary.md | docs/aiproj-track-final-evidence.md | docs/no-promotion-boundary.md | present | pass |
| final_evidence:term:https://github.com/wul012/aiproj/actions/runs/28846542546 | docs/aiproj-track-final-evidence.md | https://github.com/wul012/aiproj/actions/runs/28846542546 | present | pass |
| final_evidence:term:https://github.com/wul012/aiproj/actions/runs/28846544549 | docs/aiproj-track-final-evidence.md | https://github.com/wul012/aiproj/actions/runs/28846544549 | present | pass |
| no_promotion:term:promotion_ready=False | docs/no-promotion-boundary.md | promotion_ready=False | present | pass |
| no_promotion:term:approved_for_promotion=False | docs/no-promotion-boundary.md | approved_for_promotion=False | present | pass |
| no_promotion:term:model_quality_claim | docs/no-promotion-boundary.md | model_quality_claim | present | pass |
| no_promotion:term:lookup-only | docs/no-promotion-boundary.md | lookup-only | present | pass |
| no_promotion:term:does not automatically mean | docs/no-promotion-boundary.md | does not automatically mean | present | pass |
| doc_index:README.md:docs/aiproj-track-final-evidence.md | README.md | docs/aiproj-track-final-evidence.md | present | pass |
| doc_index:docs/README.md:aiproj-track-final-evidence.md | docs/README.md | aiproj-track-final-evidence.md | present | pass |
| doc_index:START_HERE.md:docs/aiproj-track-final-evidence.md | START_HERE.md | docs/aiproj-track-final-evidence.md | present | pass |
| doc_index:docs/script-entrypoints.md:scripts/check_aiproj_track_closeout.py | docs/script-entrypoints.md | scripts/check_aiproj_track_closeout.py | present | pass |
| ci:command:scripts/check_static_analysis.py | .github/workflows/ci.yml | scripts/check_static_analysis.py | present | pass |
| ci:command:scripts/check_type_analysis.py | .github/workflows/ci.yml | scripts/check_type_analysis.py | present | pass |
| ci:command:scripts/check_model_capability_honest_measurement.py | .github/workflows/ci.yml | scripts/check_model_capability_honest_measurement.py | present | pass |
| ci:command:scripts/check_artifact_schema_guard.py | .github/workflows/ci.yml | scripts/check_artifact_schema_guard.py | present | pass |
| ci:command:scripts/check_file_size_ratchet.py | .github/workflows/ci.yml | scripts/check_file_size_ratchet.py | present | pass |
| ci:command:scripts/check_aiproj_track_closeout.py | .github/workflows/ci.yml | scripts/check_aiproj_track_closeout.py | present | pass |
| ci:command:scripts/run_test_coverage.py --out-dir runs/test-coverage-ci --fail-under 88.98 | .github/workflows/ci.yml | scripts/run_test_coverage.py --out-dir runs/test-coverage-ci --fail-under 88.98 | present | pass |
