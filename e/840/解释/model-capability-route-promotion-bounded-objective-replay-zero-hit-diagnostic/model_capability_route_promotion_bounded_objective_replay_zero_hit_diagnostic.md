# MiniGPT model capability route promotion bounded objective replay zero-hit diagnostic

- Status: `pass`
- Decision: `model_capability_route_promotion_bounded_objective_replay_zero_hit_diagnostic_ready`
- Ready: `True`
- Zero-hit cases: `3`
- Near-miss cases: `3`
- Root causes: `4`

## Case Diagnostics

| Case | Zero Hit | Near Miss | In Corpus | Diagnosis | Action | Continuation |
| --- | --- | --- | --- | --- | --- | --- |
| canonical_direct_completion | True | fixed | True | near_miss_character_substitution_without_exact_term | probe_decoder_anchor_and_exact_prefix_bias |  wixed w |
| minimal_direct_completion | True | fixed | True | near_miss_character_substitution_without_exact_term | probe_decoder_anchor_and_exact_prefix_bias |  wixed w |
| completion_label_surface | True | fixed | True | near_miss_character_substitution_without_exact_term | probe_decoder_anchor_and_exact_prefix_bias |  wixed w |

## Root Causes

| Cause | Severity | Evidence | Detail |
| --- | --- | --- | --- |
| objective_replay_zero_required_term_hits | high | 3 | All replay rows missed fixed/loss despite a trained checkpoint. |
| near_miss_character_substitution | high | 3 | Continuations are close to required terms, for example wixed, but do not exactly hit them. |
| direct_prompts_present_but_generation_unanchored | medium | 3 | The direct objective prompts are present in corpus, so the failure is not a missing-prompt corpus gap. |
| loss_reduction_did_not_transfer_to_exact_generation | medium | -1.556213 | Training loss dropped on direct examples, but generation did not recover exact required terms. |
