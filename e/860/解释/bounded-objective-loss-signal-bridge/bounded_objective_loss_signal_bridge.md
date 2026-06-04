# MiniGPT Bounded Objective Loss Signal Bridge

- Status: `pass`
- Decision: `bounded_objective_loss_signal_bridge_ready`
- Bridge examples: `16`
- Loss-signal examples: `6`
- Fixed-signal examples: `6`
- Pair reinforcement: `4`
- Claim: `bridge_corpus_only`

## Bridge Examples

| Example | Kind | Prompt | Completion | Source |
| --- | --- | --- | --- | --- |
| longer-top20-minimal-direct-completion-loss-to-pair | loss_signal_pair_bridge | Answer with exactly two words: fixed loss answer: | fixed loss | longer-top20/minimal_direct_completion |
| longer-top20-minimal-direct-completion-loss-prefix-repair | loss_signal_prefix_repair | Answer with exactly two words: fixed loss answer: loss | fixed loss | longer-top20/minimal_direct_completion |
| longer-open-canonical-direct-completion-loss-to-pair | loss_signal_pair_bridge | Answer with exactly two tokens: fixed loss answer: | fixed loss | longer-open/canonical_direct_completion |
| longer-open-canonical-direct-completion-loss-prefix-repair | loss_signal_prefix_repair | Answer with exactly two tokens: fixed loss answer: loss | fixed loss | longer-open/canonical_direct_completion |
| longer-open-completion-label-surface-loss-to-pair | loss_signal_pair_bridge | Complete with exactly two tokens: fixed loss completion: | fixed loss | longer-open/completion_label_surface |
| longer-open-completion-label-surface-loss-prefix-repair | loss_signal_prefix_repair | Complete with exactly two tokens: fixed loss completion: loss | fixed loss | longer-open/completion_label_surface |
| v857-baseline-canonical-direct-completion-fixed-to-pair | fixed_signal_pair_bridge | Answer with exactly two tokens: fixed loss answer: | fixed loss | v857-baseline/canonical_direct_completion |
| v857-baseline-completion-label-surface-fixed-to-pair | fixed_signal_pair_bridge | Complete with exactly two tokens: fixed loss completion: | fixed loss | v857-baseline/completion_label_surface |
| top1-low-temp-canonical-direct-completion-fixed-to-pair | fixed_signal_pair_bridge | Answer with exactly two tokens: fixed loss answer: | fixed loss | top1-low-temp/canonical_direct_completion |
| top1-low-temp-completion-label-surface-fixed-to-pair | fixed_signal_pair_bridge | Complete with exactly two tokens: fixed loss completion: | fixed loss | top1-low-temp/completion_label_surface |
| top3-low-temp-completion-label-surface-fixed-to-pair | fixed_signal_pair_bridge | Complete with exactly two tokens: fixed loss completion: | fixed loss | top3-low-temp/completion_label_surface |
| longer-top20-canonical-direct-completion-fixed-to-pair | fixed_signal_pair_bridge | Answer with exactly two tokens: fixed loss answer: | fixed loss | longer-top20/canonical_direct_completion |
| pair-direct-repeat-a | pair_reinforcement | answer: | fixed loss |  |
| pair-direct-repeat-b | pair_reinforcement | completion: | fixed loss |  |
| fixed-loss-line-bridge | pair_reinforcement | fixed | loss |  |
| loss-needs-fixed-context | pair_reinforcement | loss belongs with | fixed loss |  |

## Boundary

- Reason: Loss appears in profile sweep rows, but fixed/loss co-occurrence still needs bridge training.
- Next action: `train_bounded_objective_loss_signal_bridge`
