# MiniGPT model capability route promotion bounded objective intervention plan

- Status: `pass`
- Decision: `model_capability_route_promotion_bounded_objective_intervention_plan_ready`
- Contract: `bounded_fixed_loss_direct_completion_contract`
- Next artifact: `model_capability_route_promotion_bounded_objective_contract`

## Objective Contract

| Field | Value |
| --- | --- |
| Target terms | fixed,loss |
| Canonical prompt | Answer with exactly two tokens: fixed loss answer: |
| Canonical completion | fixed loss |
| Unchanged suite check required | True |

## Work Items

| Item | Action | Output |
| --- | --- | --- |
| contract_fixture | define canonical direct-completion prompt and exact target terms | model_capability_route_promotion_bounded_objective_contract |
| direct_seed_corpus | build direct-only seed rows from the contract without carry-forward pollution | model_capability_route_promotion_bounded_objective_seed |
| controlled_training | train a tiny candidate from the objective seed with the same checkpoint evidence discipline | model_capability_route_promotion_bounded_objective_training_run |
| dual_replay | replay both the canonical contract and the unchanged v803 bounded suite | model_capability_route_promotion_bounded_objective_replay_comparison |
| fallback_decision | route to architecture capacity probe if the canonical contract still has zero required-term hits | model_capability_route_promotion_bounded_architecture_capacity_probe_plan |

## Acceptance Gates

- `contract_is_bounded`: contract contains exactly the fixed/loss target terms and no production claim
- `canonical_replay_required`: candidate must pass canonical replay before any v803 comparison matters
- `unchanged_v803_replay_required`: unchanged v803 replay remains the route-promotion check
- `architecture_fallback_defined`: zero-hit canonical replay must trigger capacity probe instead of more seed patching

## Non Goals

- `do_not_claim_v803_route_improvement_from_canonical_contract_only`
- `do_not_use_forced_prefix_or_blocked_tokens_as_promotion_evidence`
- `do_not_continue_rebalanced_decoder_profile_rescue`
