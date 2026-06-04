# MiniGPT Bounded Objective Seed Revision Curriculum Patch

- Status: `pass`
- Decision: `model_capability_route_promotion_bounded_objective_unassisted_repair_seed_revision_curriculum_patch_ready`
- Patch examples: `18`
- Loss-focus examples: `18`
- Completion-surface examples: `2`
- Patch kinds: `['completion_surface_short', 'fixed_to_loss_bridge', 'full_completion_contrast', 'loss_after_fixed_label', 'loss_after_fixed_short', 'loss_second_term_repeat', 'two_token_target_repeat']`
- Claim: `curriculum_patch_only`

## Patch Examples

| Example | Kind | Prompt | Completion | Purpose |
| --- | --- | --- | --- | --- |
| canonical_direct_completion-second-term-repeat-1 | loss_second_term_repeat | Answer with exactly two tokens: fixed loss answer: | fixed loss | repeat the full two-token target after the original contract prompt |
| canonical_direct_completion-second-term-repeat-2 | loss_second_term_repeat | Answer with exactly two tokens: fixed loss answer: | fixed loss | repeat the full two-token target after the original contract prompt |
| canonical_direct_completion-fixed-to-loss-bridge | fixed_to_loss_bridge | Answer with exactly two tokens: fixed loss answer: fixed | loss | teach loss as the immediate continuation after fixed |
| canonical_direct_completion-full-completion-contrast | full_completion_contrast | Answer with exactly two tokens: fixed loss answer: | fixed loss not: fixed t | separate full fixed loss completion from fixed t near misses |
| minimal_direct_completion-second-term-repeat-1 | loss_second_term_repeat | Answer with exactly two words: fixed loss answer: | fixed loss | repeat the full two-token target after the original contract prompt |
| minimal_direct_completion-second-term-repeat-2 | loss_second_term_repeat | Answer with exactly two words: fixed loss answer: | fixed loss | repeat the full two-token target after the original contract prompt |
| minimal_direct_completion-fixed-to-loss-bridge | fixed_to_loss_bridge | Answer with exactly two words: fixed loss answer: fixed | loss | teach loss as the immediate continuation after fixed |
| minimal_direct_completion-full-completion-contrast | full_completion_contrast | Answer with exactly two words: fixed loss answer: | fixed loss not: fixed t | separate full fixed loss completion from fixed t near misses |
| completion_label_surface-second-term-repeat-1 | loss_second_term_repeat | Complete with exactly two tokens: fixed loss completion: | fixed loss | repeat the full two-token target after the original contract prompt |
| completion_label_surface-second-term-repeat-2 | loss_second_term_repeat | Complete with exactly two tokens: fixed loss completion: | fixed loss | repeat the full two-token target after the original contract prompt |
| completion_label_surface-fixed-to-loss-bridge | fixed_to_loss_bridge | Complete with exactly two tokens: fixed loss completion: fixed | loss | teach loss as the immediate continuation after fixed |
| completion_label_surface-full-completion-contrast | full_completion_contrast | Complete with exactly two tokens: fixed loss completion: | fixed loss not: fixed t | separate full fixed loss completion from fixed t near misses |
| loss-after-fixed-short | loss_after_fixed_short | fixed | loss | short bridge for the second required term |
| loss-after-fixed-label | loss_after_fixed_label | Continue after fixed: | loss | labelled bridge for the second required term |
| two-token-target-repeat-a | two_token_target_repeat | target: | fixed loss | repeat the exact target in a compact surface |
| two-token-target-repeat-b | two_token_target_repeat | target: | fixed loss | repeat the exact target in a compact surface |
| completion-surface-short-a | completion_surface_short | completion: | fixed loss | repair completion-label prompt surface |
| completion-surface-short-b | completion_surface_short | completion: | fixed loss | repair completion-label prompt surface |

## Boundary

- Reason: The patch targets loss second-term stabilization and completion-surface zero-hit cases; capability still requires training and replay.
- Next action: `train_bounded_objective_unassisted_repair_seed_revision_curriculum_patch`
