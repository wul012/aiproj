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
| loss-internal-joint-cycle | ['fixed', 'loss'] | ['fixed'] | generation_pair_full_internal_partial |
| joint-cycle-internal-repair | [] | ['fixed', 'loss'] | internal_pair_full_generation_none |
| v630-internal-repair-resume | ['loss'] | ['fixed'] | partial_tradeoff |
| v630-light-merge-resume | ['loss'] | [] | partial_tradeoff |

## Boundary

- Model quality claim: `generation_pair_full_internal_partial`
- Reason: A route generates both terms but still has partial forced-choice internal preference.
- Next action: repair internal preference while preserving generation pair-full
