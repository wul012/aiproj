# MiniGPT Required-Term Pair Surface Policy Replay

- Status: `pass`
- Decision: `required_term_pair_surface_policy_replay_stable_pair_full_policy_found`
- Stable policies: `['dual_boundary_sentence', 'pair_context_prefix']`
- Best policy: `dual_boundary_sentence`
- Model quality claim: `decode_surface_policy_candidate`

## Policy Summary

| Policy | Pair-full seeds | Hits | Stable |
| --- | ---: | ---: | --- |
| dual_boundary_sentence | 3 | 6 | True |
| pair_context_prefix | 3 | 6 | True |
| single_label_default | 2 | 5 | False |
| single_label_suppress_newline | 2 | 5 | False |

## Boundary

- Reason: At least one replay policy produces fixed/loss pair-full across all tested seeds.
- Next action: compare stable policy leakage and minimality before promotion
