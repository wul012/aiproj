# MiniGPT model capability route promotion bounded real replay decoder anchor distribution audit

- Status: `pass`
- Decision: `model_capability_route_promotion_bounded_real_replay_decoder_anchor_distribution_needs_rebalance`
- Ready: `True`
- Examples: `48`
- Carry share: `0.5833`
- Direct share: `0.1042`
- Bridge share: `0.3125`
- Risks: `3`
- Rebalanced seed needed: `True`

## Buckets

| Bucket | Count | Share | Avg prompt chars | Avg completion chars |
| --- | --- | --- | --- | --- |
| carry_forward | 28 | 0.5833 | 76.86 | 10.0 |
| direct_answer | 5 | 0.1042 | 35.2 | 10.0 |
| decoder_bridge | 15 | 0.3125 | 39.87 | 5.33 |
| other | 0 | 0.0 | 0.0 | 0.0 |

## Risks

| Risk | Severity | Actual | Threshold | Detail |
| --- | --- | --- | --- | --- |
| direct_answer_underweighted | high | 0.1042 | 0.2 | Unanchored direct-answer rows are too sparse for a zero-hit replay failure. |
| carry_forward_dominates_seed | medium | 0.5833 | 0.5 | Carry-forward rows dominate the decoder-anchor corpus. |
| all_replay_cases_zero_hit | high | 5 | 5 | All bounded replay cases produced zero required-term hits. |
