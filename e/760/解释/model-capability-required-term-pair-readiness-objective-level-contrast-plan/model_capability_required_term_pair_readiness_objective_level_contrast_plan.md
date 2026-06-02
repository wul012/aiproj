# MiniGPT Objective-Level Contrast Plan

- Status: `pass`
- Decision: `pair_readiness_objective_level_contrast_plan_ready`
- Proposed next artifact: `pair_readiness_objective_level_contrast_contract`

## Contract Design Rows

| Row family | Count | Purpose | Guardrail |
| --- | ---: | --- | --- |
| objective-header | 6 | state the response objective before answer text | no heldout prompt surface |
| branch-role-contrast | 8 | contrast fixed/loss branch roles under explicit task ids | balanced by branch |
| pair-answer-contrast | 8 | ask for both answer terms through varied objective labels | avoid exact heldout pair prompt |
| separator-neutral-answer | 4 | separate answer terms through non-heldout separators | do not reuse fixed=\|loss= as prompt |

## Heldout Boundaries

- exact-heldout-pair prompt surface remains eval-only
- spaced-heldout-pair prompt surface remains eval-only
- arrow-heldout-pair prompt surface remains eval-only
