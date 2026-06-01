# MiniGPT Required-Term Pair Aligned-Candidate Seed Stability

- Status: `pass`
- Decision: `required_term_pair_aligned_candidate_partial_stability`
- Corpus mode: `equals_surface_no_pair_id_loss_internal_explicit_dual_boundary_repair`
- Pair-full seeds: `2/3`
- Model quality claim: `targeted_pair_refresh_partial_signal`

## Seeds

| Seed | Status | Pair full | Default full | Suppression full |
| ---: | --- | --- | ---: | ---: |
| 1535 | pass | True | 1 | 1 |
| 2535 | pass | False | 0 | 0 |
| 3535 | pass | True | 1 | 1 |

## Boundary

- Reason: Only some tested seeds reproduced generation pair-full for the aligned candidate corpus.
- Next action: score pair-full seeds internally and inspect missed seeds before promotion
