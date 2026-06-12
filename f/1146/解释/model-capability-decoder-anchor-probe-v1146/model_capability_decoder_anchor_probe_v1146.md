# MiniGPT decoder anchor probe v1146

- Generated: `2026-06-12T11:45:12Z`
- Status: `pass`
- Decision: `model_capability_decoder_anchor_probe_found_fragment_signal`

## Summary

| Metric | Value |
| --- | --- |
| decoder_anchor_probe_ready | True |
| probe_case_count | 5 |
| fragment_hit_count | 5 |
| anchor_assisted_loss_hit_count | 4 |
| fragment_hit_rate | 1.0 |
| anchor_assisted_loss_hit_rate | 0.8 |
| model_quality_claim | decoder_anchor_fragment_signal_only |
| promotion_ready | False |
| unassisted_success_claim | False |
| next_step | compare_decoder_anchor_probe_with_unassisted_holdout_replay |
| failed_check_count | 0 |

## Decoder Anchor Probe Rows

| case_id | prompt | continuation | combined | expected_fragment | fragment_hit | anchor_assisted_loss_hit | generation_error |
| --- | --- | --- | --- | --- | --- | --- | --- |
| fixed-space-loss | fixed  | lossssss | fixed lossssss | loss | True | True |  |
| lo-to-loss | lo | sssss nn | losssss nn | loss | True | True |  |
| los-to-loss | los | ssss nnn | losssss nnn | loss | True | True |  |
| fixed-retention | fixed |  fixe fi | fixed fixe fi | fixed | True | False |  |
| fi-to-loss-association | fi | er losss | fier losss | loss | True | True |  |

## Recommendations

- Treat v1146 as anchor-assisted fragment evidence only.
- Compare this checkpoint against unassisted holdout replay before claiming broader model improvement.
