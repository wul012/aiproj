# MiniGPT Pair Prompt Transfer Repair Plan

- Status: `pass`
- Decision: `pair_readiness_pair_prompt_transfer_repair_plan_ready`
- Next artifact: `pair_readiness_pair_prompt_transfer_contract_patch`

## Repair Requirements

- add surrogate pair-transfer rows that bind fixed and loss in one training line without using the exact heldout pair probe
- cover more than one non-heldout separator style so transfer is not tied to a single string template
- preserve fixed=fixed and loss=loss direct-completion rows from the base contract
- keep heldout pair prompt fixed=|loss= out of training rows and materialized corpus lines
- require pair-probe replay before any promotion claim

## Checks

| Check | Status | Actual | Detail |
| --- | --- | --- | --- |
| pair_probe_replay_passed | pass | pass | pair-probe replay must execute successfully |
| pair_probe_not_ready | pass | pair_readiness_direct_completion_pair_probe_replay_not_ready | repair follows only the not-ready direct-completion pair-probe replay result |
| exact_pair_failed | pass | False | exact heldout pair prompt must be the observed failure |
| no_pair_prompt_full | pass | 0 | plan assumes no pair prompt surface replayed pair-full |
| heldout_pair_remains_heldout | pass | fixed=\|loss= | heldout pair prompt identity must stay explicit |
