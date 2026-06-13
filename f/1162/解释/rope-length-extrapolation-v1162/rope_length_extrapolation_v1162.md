# MiniGPT learned-vs-RoPE position behavior beyond trained length v1162

- Generated: `2026-06-13T16:04:26Z`
- Status: `pass`
- Decision: `length_extrapolation_measured`

## Summary

| Metric | Value |
| --- | --- |
| status | pass |
| decision | length_extrapolation_measured |
| verdict | absolute_index_definedness_gap_confirmed |
| device | cuda |
| seeds | 5 |
| train_block_size | 32 |
| model_block_size | 128 |
| eval_lengths | 32,48,64,96,128 |
| n_layer | 4 |
| n_head | 4 |
| n_embd | 128 |
| steps | 400 |
| weight_decay | 0.0 |
| train_char_count | 34160 |
| heldout_char_count | 11408 |
| learned_jump_at_max_mean | 0.122316 |
| learned_jump_at_max_std | 0.01908 |
| rope_jump_at_max_mean | 0.004205 |
| rope_jump_at_max_std | 0.000888 |
| within_range_control_learned | 0.777587 |
| within_range_control_rope | 0.778322 |
| sliding_window_learned_loss | 0.776698 |
| sliding_window_learned_loss_std | 0.001168 |
| rope_within_range_loss | 0.778322 |
| learned_beyond_random_tail_at_max | 0.896117 |
| learned_beyond_zeroed_tail_at_max | 0.791471 |
| learned_beyond_noise_component | 0.104646 |
| learned_beyond_signal_component | 0.013884 |
| learned_beyond_degradation_source | mostly random-noise injection from untrained rows |
| rope_attention_mass_beyond_trained_distance | 0.393902 |
| untrained_tail_l2_drift_max | 0.0 |
| both_schemes_raise_beyond_block_size | True |
| both_schemes_finite_when_rebuilt | True |
| beyond_range_token_count_min | 18960 |
| learned_position_table_params | 16384 |
| rope_effective_position_params | 0 |

## Rows

| scheme | eval_length | within_loss_mean | within_loss_std | beyond_loss_mean | beyond_loss_std | beyond_minus_within_mean | beyond_minus_within_std | within_token_count | beyond_token_count | window_count |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| learned | 32 | 0.777587 | 0.001299 |  |  |  |  | 11407 | 0 | 357 |
| rope | 32 | 0.778322 | 0.001236 |  |  |  |  | 11407 | 0 | 357 |
| learned | 48 | 0.777369 | 0.001246 | 0.88878 | 0.021885 | 0.111411 | 0.02075 | 7615 | 3792 | 238 |
| rope | 48 | 0.778104 | 0.001263 | 0.77845 | 0.001691 | 0.000346 | 0.001361 | 7615 | 3792 | 238 |
| learned | 64 | 0.7754 | 0.001575 | 0.896204 | 0.028077 | 0.120804 | 0.027416 | 5711 | 5696 | 179 |
| rope | 64 | 0.776116 | 0.001337 | 0.78006 | 0.001111 | 0.003944 | 0.000855 | 5711 | 5696 | 179 |
| learned | 96 | 0.777194 | 0.001171 | 0.901388 | 0.027064 | 0.124194 | 0.026568 | 3808 | 7599 | 119 |
| rope | 96 | 0.777981 | 0.001145 | 0.777611 | 0.001228 | -0.00037 | 0.000442 | 3808 | 7599 | 119 |
| learned | 128 | 0.773802 | 0.001554 | 0.896117 | 0.019263 | 0.122316 | 0.01908 | 2863 | 8544 | 90 |
| rope | 128 | 0.774469 | 0.001317 | 0.778674 | 0.001074 | 0.004205 | 0.000888 | 2863 | 8544 | 90 |

## Recommendations

- VERDICT (absolute_index_definedness_gap_confirmed): at the longest eval length 128, the learned-position beyond-range loss rises +0.1223±0.0191 nats above its within-range loss, while RoPE moves +0.0042±0.0009. Only the SIGN is pre-registered; the magnitude is measured over 5 seeds.
- SCOPE — this measures whether each scheme stays FUNCTIONAL/DEFINED at lengths > train length, NOT whether longer context helps. The corpus is independent ~11-char sentences with no cross-sentence dependency, so no prediction needs more than ~11 tokens of history.
- NOT relative-distance extrapolation: every signal-bearing relative offset at the beyond-range indices (<=~11, intra-sentence) was already seen during training. The only thing novel there is the ABSOLUTE index, which RoPE ignores by construction; the learned table simply has untrained rows there.
- The seq_len>block_size ValueError fires identically for BOTH schemes (it is gated on block_size and the block_size×block_size mask buffer). A RoPE model built at the small block_size also raises; both raise=True, both finite when rebuilt=True. RoPE's real edge is that enlarging the ceiling costs ZERO position params and zero retraining; the learned table needs block_size trainable rows.
- Realistic learned deployment = sliding window of 32: loss 0.7767 vs RoPE within-range 0.7783. On this no-long-range corpus it roughly ties RoPE, so the naive-long-forward gap is an inference-mode artifact, not an inherent learned-positions deficiency.
- Zeroed-tail diagnostic at length 128: random-init tail 0.8961 -> zeroed tail 0.7915 -> within-range 0.7776. Decomposition = mostly random-noise injection from untrained rows: noise-injection component +0.1046 (recovered by zeroing the untrained rows) vs residual missing-signal component +0.0139.
- Untrained tail max L2 drift across seeds = 0.00e+00 (weight_decay=0.0), so the beyond-range rows are provably at their N(0,0.02) init.
- Naive RoPE (Llama form, base=10000, no NTK/YaRN) is itself known to degrade on relative distances beyond training; ~39.4% of attention mass at length 128 lands on relative distances > 32, but those distances carry no signal in this corpus so the degradation cannot be exposed here.
- Parameter framing: the RoPE model still ALLOCATES an unused position table, so an equal total parameter count is incidental — RoPE's effective position params are 0. A future cleanup could drop the unused table.
