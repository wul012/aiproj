# MiniGPT model capability route promotion bounded objective contract

- Status: `pass`
- Decision: `model_capability_route_promotion_bounded_objective_contract_ready`
- Contract: `bounded_fixed_loss_direct_completion_contract`
- Next artifact: `model_capability_route_promotion_bounded_objective_seed`

## Contract

| Field | Value |
| --- | --- |
| Target terms | fixed,loss |
| Canonical prompt | Answer with exactly two tokens: fixed loss answer: |
| Required completion | fixed loss |
| Unchanged suite required | True |

## Contract Cases

| Case | Prompt | Completion | Canonical |
| --- | --- | --- | --- |
| canonical_direct_completion | Answer with exactly two tokens: fixed loss answer: | fixed loss | True |
| minimal_direct_completion | Answer with exactly two words: fixed loss answer: | fixed loss | False |
| completion_label_surface | Complete with exactly two tokens: fixed loss completion: | fixed loss | False |

## Seed Blueprint

- Blueprint: `bounded_objective_direct_seed_v837_blueprint`
- Planned examples: `18`
- Next artifact: `model_capability_route_promotion_bounded_objective_seed`

## Holdout Rule

- `unchanged_v803_bounded_suite_holdout`: canonical contract success is not enough for route promotion; unchanged v803 bounded replay must remain visible
