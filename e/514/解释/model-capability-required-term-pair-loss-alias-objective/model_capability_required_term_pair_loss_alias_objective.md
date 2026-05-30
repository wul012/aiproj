# MiniGPT Required-Term Pair Loss-Alias Objective

- Status: `pass`
- Decision: `required_term_pair_loss_alias_continuation_full_hit`
- Loss alias decision: `loss_alias_heldout_full_hit`
- Training status: `pass`
- Checkpoint: `e\514\解释\model-capability-required-term-pair-loss-alias-objective\loss-alias-run\checkpoint.pt`
- Heldout loss alias hits: `3/3`
- Full heldout coverage: `True`

## Case Summary

| Case | Type | Prompt | Source hits | Candidate hits |
| --- | --- | --- | ---: | ---: |
| source-loss | source | loss: | 0 | 1 |
| heldout-beta-loss | heldout | beta: | 0 | 1 |
| heldout-omega-loss | heldout | omega: | 0 | 1 |
| heldout-theta-loss | heldout | theta: | 0 | 1 |

## Generation Rows

| Case | Hit | Continuation |
| --- | --- | --- |
| source-loss | True | lossssssssss |
| heldout-beta-loss | True | lossssssssss |
| heldout-omega-loss | True | lossssssssss |
| heldout-theta-loss | True | lossssssssss |

## Boundary

- Model quality claim: `tiny_loss_alias_heldout_full_signal`
- Reason: The tiny loss-alias run emitted loss for every held-out loss alias prompt.
- Next action: repeat the loss-alias objective across seeds before promoting the recovery
