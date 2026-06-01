# MiniGPT Loss-Internal-Preference Route Decision

- Status: `pass`
- Decision: `select_loss_internal_first_token_for_decode_bridge_not_promotion`
- Decode bridge source: `loss-internal-first-token`
- Internal bridge required: `True`

## Routes

| Route | Generation Pair | Forced Choice Pair | Bridge | Rejections |
| --- | --- | --- | --- | --- |
| loss-internal-preference | False | False | False | ['generation_not_pair_full', 'forced_choice_not_pair_full', 'fixed_only_generation'] |
| loss-internal-first-token | False | True | True | ['generation_not_pair_full', 'loss_only_generation'] |
| loss-internal-ranked-choice | False | False | False | ['generation_not_pair_full', 'forced_choice_not_pair_full', 'fixed_only_generation'] |

## Boundary

- Model quality claim: `internal_pair_match_not_generation_pair_full`
- Reason: The selected route has internal pair match but no generation pair-full.
- Next action: build a decode bridge check around the selected first-token checkpoint
