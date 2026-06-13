# MiniGPT RoPE vs learned positions held-out comparison v1160

- Generated: `2026-06-13T14:00:29Z`
- Status: `pass`
- Decision: `rope_capability_validated`

## Summary

| Metric | Value |
| --- | --- |
| status | pass |
| decision | rope_capability_validated |
| verdict | learned_positions_lower_heldout_loss |
| device | cuda |
| steps | 400 |
| block_size | 48 |
| n_layer | 4 |
| n_head | 4 |
| n_embd | 128 |
| heldout_token_count | 890 |
| train_char_count | 3562 |
| heldout_char_count | 891 |
| learned_heldout_loss | 0.898242 |
| rope_heldout_loss | 1.01731 |
| heldout_loss_delta_rope_minus_learned | 0.119067 |
| learned_heldout_accuracy | 0.680899 |
| rope_heldout_accuracy | 0.678652 |
| heldout_accuracy_delta | -0.002247 |

## Rows

| positional_scheme | heldout_loss | heldout_token_accuracy | parameter_count |
| --- | --- | --- | --- |
| learned_absolute | 0.898242 | 0.680899 | 807680 |
| rope | 1.01731 | 0.678652 | 807680 |

## Recommendations

- Both positional schemes trained to a real held-out loss; verdict: learned_positions_lower_heldout_loss (RoPE - learned = +0.1191 loss, -0.0022 accuracy).
- RoPE encodes relative position by rotating Q/K and needs no learned position table; on this short fixed-length corpus its main practical edge (length extrapolation) is not yet exercised — that is a candidate for a later version.
- Note: the RoPE model still allocates an unused position_embedding for state_dict simplicity; a future cleanup could drop it to realize RoPE's parameter saving.
