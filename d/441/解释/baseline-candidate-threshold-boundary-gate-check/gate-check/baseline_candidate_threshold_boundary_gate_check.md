# MiniGPT Baseline-Candidate Threshold Boundary Gate Check

- Status: `pass`
- Decision: `expected_exit_verified`
- Gate mode: `diagnosis_strict`
- Actual exit code: `2`
- Expected exit code: `2`
- Diagnosis: `candidate_not_accepted`
- Failed checks: `0`

| Check | Status | Expected | Actual |
| --- | --- | --- | --- |
| summary_exists | pass | True | True |
| summary_loads | pass | loadable JSON object | loaded |
| summary_status_pass | pass | True | pass |
| summary_expected_exit_matches | pass | 2 | 2 |
| actual_exit_matches_expected | pass | 2 | 2 |
| diagnosis_decision_matches | pass | candidate_not_accepted | candidate_not_accepted |
