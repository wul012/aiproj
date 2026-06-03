# MiniGPT model capability route promotion bounded real replay failure alignment diagnostic

- Status: `pass`
- Decision: `model_capability_route_promotion_bounded_real_replay_failure_alignment_diagnostic_ready`
- Ready: `True`
- Failed cases: `5/5`
- Prompt gaps: `2`
- Root causes: `3`

## Case Diagnostics

| Case | Prompt in corpus | Repair pass | Missed terms | Diagnosis | Action |
| --- | --- | --- | --- | --- | --- |
| objective-answer-direct | True | False | fixed,loss | required_terms_present_but_generation_not_anchored | add_decoder_anchoring_examples_or_adjust_decoding |
| objective-answer-role | True | False | fixed,loss | required_terms_present_but_generation_not_anchored | add_decoder_anchoring_examples_or_adjust_decoding |
| objective-answer-contrast | False | False | fixed,loss | benchmark_prompt_not_represented_in_training_corpus | add_exact_benchmark_prompt_completion_examples |
| objective-answer-jsonish | False | False | fixed,loss | benchmark_prompt_not_represented_in_training_corpus | add_exact_benchmark_prompt_completion_examples |
| objective-answer-check | True | False | fixed,loss | required_terms_present_but_generation_not_anchored | add_decoder_anchoring_examples_or_adjust_decoding |

## Root Causes

| Cause | Severity | Evidence | Detail |
| --- | --- | --- | --- |
| benchmark_prompt_training_corpus_gap | high | 2 | Benchmark prompts are not exactly represented in the revised training corpus. |
| repair_training_not_replay_aligned | high | -0.4 | Training produced a checkpoint, but bounded replay still regressed against baseline. |
| loss_improvement_not_sufficient_for_exact_terms | medium | 3.9442343711853027 | Loss evidence is not enough for fixed/loss exact-term generation. |
