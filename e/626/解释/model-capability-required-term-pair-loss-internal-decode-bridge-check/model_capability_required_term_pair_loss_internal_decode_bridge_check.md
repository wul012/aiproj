# MiniGPT Loss-Internal Decode Bridge Check

- Status: `pass`
- Decision: `loss_internal_decode_bridge_gap_confirmed`
- Selected source: `loss-internal-first-token`
- Bridge gap terms: `['fixed']`
- Decode bridge ready: `True`

## Bridge Rows

| Term | Generation Hit | Internal Best | Bridge Gap | Best Candidate |
| --- | --- | --- | --- | --- |
| fixed | False | True | True | fixed |
| loss | True | True | False | loss |

## Boundary

- Model quality claim: `decode_bridge_gap_evidence`
- Reason: The selected checkpoint has internal pair match but generation misses at least one term.
- Next action: train a bridge objective that preserves internal loss while restoring the missed generation term
