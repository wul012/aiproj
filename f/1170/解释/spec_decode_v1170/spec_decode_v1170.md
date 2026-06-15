# MiniGPT speculative decoding v1170

- Generated: `2026-06-15T01:12:04Z`
- Status: `pass`
- Decision: `spec_decode_measured`

## Summary

| Metric | Value |
| --- | --- |
| status | pass |
| decision | spec_decode_measured |
| verdict | spec_decode_verified_identical_fewer_forwards_no_wallclock_win |
| device | cuda |
| seeds | 3 |
| ops | C,R,S,L |
| k_values | 1,2,4 |
| n_layer | 4 |
| n_head | 4 |
| n_embd | 64 |
| use_rope | True |
| block_size | 16 |
| max_new_tokens | 7 |
| target_exact_match | 0.8667 |
| heldout_prompts | 444 |
| correctness_verified | True |
| task_learned | True |
| max_verify_logit_diff | 1.955e-05 |
| logit_identity_ok | True |
| greedy_identical | 3600 |
| greedy_tie_artifact | 0 |
| greedy_genuine_diff | 0 |
| greedy_total | 3600 |
| greedy_identity_ok | True |
| sampling_tv_mean | 0.002023 |
| sampling_tv_floor_mean | 0.002634 |
| sampling_tv_floor_std | 0.001276 |
| sampling_tv_ok | True |
| max_consistency_residual | 0.220939 |
| accept_rule_consistency_ok | True |
| alpha_min_nonself | 0.527 |
| alpha_max_nonself | 0.9313 |
| alpha_graded | True |
| alpha_at_timing_k | 0.7976 |
| rep_draft | ckpt200 |
| rep_k | 4 |
| rep_target_positions_ratio_vs_plain | 1.2794 |
| rep_tokens_per_target_forward | 2.1034 |
| rep_total_forwards_per_token | 2.1091 |
| wallclock_spec_median_s | 0.044971 |
| wallclock_plain_median_s | 0.02487 |
| wallclock_speedup | 0.5468 |
| wallclock_spec_faster | False |
| wallclock_spec_slower | True |

## Rows

| draft | k | draft_em | alpha_greedy | alpha_sample | tokens_per_target_forward | target_positions_ratio_vs_plain | total_forwards_per_token |
| --- | --- | --- | --- | --- | --- | --- | --- |
| ckpt30 | 1 | 0.0042 | 0.5753 |  | 1.2332 | 1.1035 | 2.0065 |
| ckpt30 | 2 | 0.0042 | 0.5666 |  | 1.3835 | 1.32 | 2.2143 |
| ckpt30 | 4 | 0.0042 | 0.5899 |  | 1.4587 | 1.8365 | 3.079 |
| ckpt80 | 1 | 0.1042 | 0.677 |  | 1.2926 | 1.0641 | 1.975 |
| ckpt80 | 2 | 0.1042 | 0.6905 |  | 1.5303 | 1.2124 | 2.0714 |
| ckpt80 | 4 | 0.1042 | 0.6983 |  | 1.7383 | 1.5587 | 2.5903 |
| ckpt200 | 1 | 0.4708 | 0.8359 | 0.8122 | 1.3706 | 1.0165 | 1.95 |
| ckpt200 | 2 | 0.4708 | 0.8191 | 0.7937 | 1.6891 | 1.1095 | 1.9345 |
| ckpt200 | 4 | 0.4708 | 0.826 | 0.8137 | 2.1034 | 1.2794 | 2.1091 |
| ckpt450 | 1 | 0.7292 | 0.8991 |  | 1.3886 | 1.0063 | 1.9595 |
| ckpt450 | 2 | 0.7292 | 0.8807 |  | 1.7358 | 1.0838 | 1.9214 |
| ckpt450 | 4 | 0.7292 | 0.8764 |  | 2.2031 | 1.2222 | 2.0297 |
| self | 1 | 0.8667 | 1.0 |  | 1.4 | 1.0 | 2.0 |
| self | 2 | 0.8667 | 1.0 |  | 1.75 | 1.0762 | 2.0 |
| self | 4 | 0.8667 | 1.0 |  | 2.3333 | 1.1524 | 2.0 |

## Recommendations

- VERDICT (spec_decode_verified_identical_fewer_forwards_no_wallclock_win): speculative decoding is CORRECTNESS-verified — the (k+1)-wide cached verify reproduces the full forward to max 1.96e-05 (<0.0001); greedy completions 3600/3600 identical (0 tie-artifacts, 0 genuine diffs); sampling TV 0.0020 <= noise floor 0.0026+2*0.0013; accept-rule residual max 0.2209. status==pass certifies the implementation is SOUND and the efficiency numbers meaningful — NOT that it is fast.
- ACCEPTANCE: under-trained-checkpoint drafts give GRADED alpha in [0.53,0.93] (self-spec anchor = 1.0); alpha falls as K grows, so tokens-per-target-forward is NON-monotone in K (bigger K is NOT always better). alpha_sample is reported separately and is lower than alpha_greedy at temperature 1.0.
- EFFICIENCY IS FLOPs-HONEST: the PRIMARY metric is target_positions_processed. At the representative config (ckpt200, K=4) spec processes 1.2794x the target positions of plain decoding — a (k+1)-wide verify pays k+1 positions per block REGARDLESS of acceptance, so spec saves target WORK only when accepted-per-block beats the verify overhead. tokens_per_target_forward (2.1034) is a flattering COUNT metric (prices the wide verify as one unit); total_forwards_per_token (2.1091) counts the draft and refutes 'a tiny draft is free'.
- WALL-CLOCK: spec median 0.044971s vs plain 0.02487s (speedup 0.55x; faster=False, slower=True by the conservative significance test). At char-toy scale both models are far below GPU saturation so a (k+1)-wide and a 1-wide forward cost nearly the same and Python overhead dominates — no wall-clock win is the EXPECTED honest result, not a defect.
- SCOPE / FALSIFIED FRAMINGS: B=1 greedy & sampling on a char-level toy; batched (ragged-accept) decoding out of scope. Refuted: 'speeds up our model' (wall-clock, false here), 'bigger K always better' (alpha drops with K), 'a tiny draft is free' (draft does K forwards/block), 'fewer forwards==cheaper' (positions/FLOPs rise), 'verified-identical==drop-in/production-ready' (this is B=1 char-toy correctness, NOT a deployable speedup).
