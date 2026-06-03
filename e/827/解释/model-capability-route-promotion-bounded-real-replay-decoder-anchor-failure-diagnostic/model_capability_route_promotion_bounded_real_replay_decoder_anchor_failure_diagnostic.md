# MiniGPT model capability route promotion bounded real replay decoder anchor failure diagnostic

- Status: `pass`
- Decision: `model_capability_route_promotion_bounded_real_replay_decoder_anchor_failure_diagnostic_ready`
- Ready: `True`
- Failed cases: `5/5`
- Zero-hit cases: `5`
- Fragment-like cases: `5`
- Root causes: `4`

## Case Diagnostics

| Case | Pass | Prompt in corpus | Zero hit | Fragment-like | Missed terms | Diagnosis | Action |
| --- | --- | --- | --- | --- | --- | --- | --- |
| objective-answer-direct | False | True | True | True | fixed,loss | character_fragmentation_without_term_anchoring | audit_decoder_anchor_distribution_and_sampling |
| objective-answer-role | False | True | True | True | fixed,loss | character_fragmentation_without_term_anchoring | audit_decoder_anchor_distribution_and_sampling |
| objective-answer-contrast | False | True | True | True | fixed,loss | character_fragmentation_without_term_anchoring | audit_decoder_anchor_distribution_and_sampling |
| objective-answer-jsonish | False | True | True | True | fixed,loss | character_fragmentation_without_term_anchoring | audit_decoder_anchor_distribution_and_sampling |
| objective-answer-check | False | True | True | True | fixed,loss | character_fragmentation_without_term_anchoring | audit_decoder_anchor_distribution_and_sampling |

## Root Causes

| Cause | Severity | Evidence | Detail |
| --- | --- | --- | --- |
| decoder_anchor_examples_present_but_replay_zero_hit | high | {'bridge': 15, 'direct': 5} | The corpus contains decoder-anchor bridge/direct examples, but replay still misses fixed/loss. |
| zero_required_term_hits | high | 5 | Decoder-anchor checkpoint continuations did not contain any expected required terms. |
| character_fragmentation_dominates_generation | medium | 5 | Continuations contain scattered character fragments instead of complete required terms. |
| loss_reduction_did_not_transfer_to_bounded_replay | medium | 4.262609481811523 | The decoder-anchor run trained successfully, but replay still failed against baseline. |
