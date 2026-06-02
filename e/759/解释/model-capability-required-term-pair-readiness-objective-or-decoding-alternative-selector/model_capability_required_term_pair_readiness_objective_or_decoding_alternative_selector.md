# MiniGPT Objective-Or-Decoding Alternative Selector

- Status: `pass`
- Decision: `pair_readiness_objective_or_decoding_alternative_selected`
- Selected route: `objective_level_contrast`
- Proposed next artifact: `pair_readiness_objective_level_contrast_plan`

## Route Scores

| Route | Score | Selected | Next artifact | Risk control |
| --- | ---: | --- | --- | --- |
| objective_level_contrast | 92 | True | pair_readiness_objective_level_contrast_plan | keep heldout exact pair prompts out of training rows |
| decode_side_constraint_probe | 78 | False | pair_readiness_decode_side_constraint_probe | report as diagnostic only; do not treat constrained hits as promotion |
| fresh_seed_stability | 64 | False | pair_readiness_fresh_seed_stability_replay | run after a selected objective/decoding route has a concrete hypothesis |

## Non Goals

- do not add more near-exact surface rows
- do not promote constrained decoding as model-quality proof
- do not start fresh-seed training without a sharper route hypothesis
