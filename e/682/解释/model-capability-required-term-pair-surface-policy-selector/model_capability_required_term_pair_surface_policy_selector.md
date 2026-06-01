# MiniGPT Required-Term Pair Surface Policy Selector

- Status: `pass`
- Decision: `required_term_pair_surface_policy_selected_for_minimality_check`
- Selected policy: `pair_context_prefix`
- Promotion ready: `False`
- Model quality claim: `decode_surface_policy_selected_not_promoted`

## Candidates

| Policy | Stable | Leakage | Boundary wording | Score | Reason |
| --- | --- | --- | --- | ---: | --- |
| dual_boundary_sentence | True | contextual_anchor | True | 25 | stable but longer and tied to training boundary wording |
| pair_context_prefix | True | contextual_anchor | False | 47 | stable contextual anchor with shorter prompt template |
| single_label_default | False | none | False | -1000 | not stable across seeds |
| single_label_suppress_newline | False | none | False | -1000 | not stable across seeds |

## Boundary

- Reason: A stable contextual policy was selected by leakage rank and prompt minimality, but it is not promotion-ready.
- Next action: run minimality and leakage checks for the selected policy
