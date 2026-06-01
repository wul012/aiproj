# MiniGPT Generation/Internal Alignment Comparison

- Status: `pass`
- Decision: `keep_generation_pair_full_and_repair_internal_preference`
- Generation pair-full: `1`
- Internal pair-full: `2`
- Aligned pair-full: `0`
- Best sources: `['loss-internal-first-token', 'loss-internal-joint-cycle']`

## Source Rows

| Route | Generation | Internal | Class |
| --- | --- | --- | --- |
| loss-internal-first-token | ['loss'] | ['fixed', 'loss'] | internal_pair_full_generation_gap |
| loss-internal-fixed-bridge | ['fixed'] | ['fixed'] | fixed_only_aligned_partial |
| loss-internal-joint-cycle | ['fixed', 'loss'] | ['fixed'] | generation_pair_full_internal_partial |
| loss-internal-balanced-anchor | ['fixed'] | ['fixed'] | fixed_only_aligned_partial |
| joint-cycle-internal-repair | [] | ['fixed', 'loss'] | internal_pair_full_generation_none |
| joint-cycle-light-merge | ['loss'] | ['fixed'] | partial_tradeoff |
| surface-first-schedule | ['fixed'] | ['fixed'] | fixed_only_aligned_partial |

## Boundary

- Model quality claim: `generation_pair_full_internal_partial`
- Reason: A route generates both terms but still has partial forced-choice internal preference.
- Next action: repair internal preference while preserving generation pair-full
