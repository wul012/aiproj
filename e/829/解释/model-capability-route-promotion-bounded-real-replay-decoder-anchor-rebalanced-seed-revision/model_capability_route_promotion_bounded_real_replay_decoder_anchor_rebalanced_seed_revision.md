# MiniGPT model capability route promotion bounded real replay decoder anchor rebalanced seed revision

- Status: `pass`
- Decision: `model_capability_route_promotion_bounded_real_replay_decoder_anchor_rebalanced_seed_revision_ready`
- Ready: `True`
- Examples: `40`
- Carry share: `0.25`
- Direct share: `0.375`
- Bridge share: `0.375`
- Dropped carry-forward: `18`
- Added direct-answer: `10`

## Buckets

| Bucket | Count | Share |
| --- | --- | --- |
| carry_forward | 10 | 0.25 |
| direct_answer | 15 | 0.375 |
| decoder_bridge | 15 | 0.375 |
| other | 0 | 0.0 |

## Rebalance Rows

| Case | Kept carry | Dropped carry | Added direct | Bridge |
| --- | --- | --- | --- | --- |
| objective-answer-check | 2 | 4 | 2 | 3 |
| objective-answer-contrast | 2 | 3 | 2 | 3 |
| objective-answer-direct | 2 | 4 | 2 | 3 |
| objective-answer-jsonish | 2 | 3 | 2 | 3 |
| objective-answer-role | 2 | 4 | 2 | 3 |
