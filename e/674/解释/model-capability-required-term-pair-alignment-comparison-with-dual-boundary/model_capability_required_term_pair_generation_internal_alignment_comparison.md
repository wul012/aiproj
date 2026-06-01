# MiniGPT Generation/Internal Alignment Comparison

- Status: `pass`
- Decision: `select_aligned_generation_internal_pair_full_candidate`
- Generation pair-full: `2`
- Internal pair-full: `3`
- Aligned pair-full: `1`
- Best sources: `['dual-boundary-seed-3535']`

## Source Rows

| Route | Generation | Internal | Class |
| --- | --- | --- | --- |
| loss-internal-first-token | ['loss'] | ['fixed', 'loss'] | internal_pair_full_generation_gap |
| loss-internal-joint-cycle | ['fixed', 'loss'] | ['fixed'] | generation_pair_full_internal_partial |
| joint-cycle-internal-repair | [] | ['fixed', 'loss'] | internal_pair_full_generation_none |
| v630-internal-repair-resume | ['loss'] | ['fixed'] | partial_tradeoff |
| v630-light-merge-resume | ['loss'] | [] | partial_tradeoff |
| dual-boundary-seed-3535 | ['fixed', 'loss'] | ['fixed', 'loss'] | generation_internal_pair_full |

## Boundary

- Model quality claim: `targeted_pair_alignment_candidate`
- Reason: At least one route has both generation pair-full and internal pair-full.
- Next action: repeat the aligned candidate across seeds before promotion
