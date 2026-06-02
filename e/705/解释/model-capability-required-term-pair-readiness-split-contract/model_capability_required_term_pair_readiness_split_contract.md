# MiniGPT Required-Term Pair-Readiness Split Contract

- Status: `pass`
- Decision: `pair_readiness_split_contract_ready`
- Heldout pair probe: `fixed=|loss=`
- Model quality claim: `contract_only`

## Checks

| Check | Status | Actual | Detail |
| --- | --- | --- | --- |
| plan_passed | pass | pass | split plan must pass |
| plan_decision | pass | pair_readiness_split_plan_ready | contract follows only a ready pair-readiness split plan |
| next_artifact_matches | pass | pair_readiness_split_contract | plan must request this contract artifact |
| training_rows_present | pass | 12 | contract needs direct and anti-contamination rows |
| evaluation_probes_present | pass | 3 | contract needs fixed, loss, and pair heldout probes |
| no_exact_eval_row_overlap | pass | [] | evaluation prompt strings must not be exact training rows |
| heldout_pair_probe_absent | pass | False | heldout pair probe must stay out of training rows |

## Training Rows

- `fixed=f`
- `fixed=fi`
- `fixed=fix`
- `fixed=fixed`
- `loss=l`
- `loss=lo`
- `loss=los`
- `loss=loss`
- `fixed branch starts with f`
- `loss branch starts with l`
- `fixed branch does not start loss`
- `loss branch does not start fixed`
