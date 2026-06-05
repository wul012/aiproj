# MiniGPT bounded objective loss signal bridge target-only memory stagnation-aware suffix patch

- Status: `pass`
- Decision: `bounded_objective_loss_signal_bridge_target_only_memory_stagnation_aware_suffix_patch_ready`
- Patch examples: `27`
- Suffix-position examples: `12`
- Surface-format examples: `4`
- Decoder anchors: `0`
- Next step: `train_bounded_objective_loss_signal_bridge_target_only_memory_stagnation_aware_suffix_patch`

## Patch Examples

| Example | Kind | Source case | Purpose | Text |
| --- | --- | --- | --- | --- |
| canonical_direct_completion-space-exact | replay_prompt_boundary | canonical_direct_completion | space exact contract completion | Answer with exactly two tokens: fixed loss answer: fixed loss |
| canonical_direct_completion-newline-exact | replay_prompt_boundary | canonical_direct_completion | newline exact contract completion | Answer with exactly two tokens: fixed loss answer: fixed loss |
| canonical_direct_completion-fixed-l-loss-space | suffix_position | canonical_direct_completion | force loss after fixed-l fragment | Answer with exactly two tokens: fixed loss answer: fixed l loss fixed loss |
| canonical_direct_completion-fixed-l-loss-newline | suffix_position | canonical_direct_completion | force loss after newline fixed-l fragment | Answer with exactly two tokens: fixed loss answer: fixed l loss fixed loss |
| canonical_direct_completion-fixed-lo-loss-space | suffix_position | canonical_direct_completion | force loss after fixed-lo fragment | Answer with exactly two tokens: fixed loss answer: fixed lo loss fixed loss |
| canonical_direct_completion-fixed-lo-loss-newline | suffix_position | canonical_direct_completion | force loss after newline fixed-lo fragment | Answer with exactly two tokens: fixed loss answer: fixed lo loss fixed loss |
| minimal_direct_completion-space-exact | replay_prompt_boundary | minimal_direct_completion | space exact contract completion | Answer with exactly two words: fixed loss answer: fixed loss |
| minimal_direct_completion-newline-exact | replay_prompt_boundary | minimal_direct_completion | newline exact contract completion | Answer with exactly two words: fixed loss answer: fixed loss |
| minimal_direct_completion-fixed-l-loss-space | suffix_position | minimal_direct_completion | force loss after fixed-l fragment | Answer with exactly two words: fixed loss answer: fixed l loss fixed loss |
| minimal_direct_completion-fixed-l-loss-newline | suffix_position | minimal_direct_completion | force loss after newline fixed-l fragment | Answer with exactly two words: fixed loss answer: fixed l loss fixed loss |
| minimal_direct_completion-fixed-lo-loss-space | suffix_position | minimal_direct_completion | force loss after fixed-lo fragment | Answer with exactly two words: fixed loss answer: fixed lo loss fixed loss |
| minimal_direct_completion-fixed-lo-loss-newline | suffix_position | minimal_direct_completion | force loss after newline fixed-lo fragment | Answer with exactly two words: fixed loss answer: fixed lo loss fixed loss |
| completion_label_surface-space-exact | replay_prompt_boundary | completion_label_surface | space exact contract completion | Complete with exactly two tokens: fixed loss completion: fixed loss |
| completion_label_surface-newline-exact | replay_prompt_boundary | completion_label_surface | newline exact contract completion | Complete with exactly two tokens: fixed loss completion: fixed loss |
| completion_label_surface-fixed-l-loss-space | suffix_position | completion_label_surface | force loss after fixed-l fragment | Complete with exactly two tokens: fixed loss completion: fixed l loss fixed loss |
| completion_label_surface-fixed-l-loss-newline | suffix_position | completion_label_surface | force loss after newline fixed-l fragment | Complete with exactly two tokens: fixed loss completion: fixed l loss fixed loss |
| completion_label_surface-fixed-lo-loss-space | suffix_position | completion_label_surface | force loss after fixed-lo fragment | Complete with exactly two tokens: fixed loss completion: fixed lo loss fixed loss |
| completion_label_surface-fixed-lo-loss-newline | suffix_position | completion_label_surface | force loss after newline fixed-lo fragment | Complete with exactly two tokens: fixed loss completion: fixed lo loss fixed loss |
| surface-answer-space | surface_format | global | preserve space answer surface | answer: fixed loss |
| surface-answer-newline | surface_format | global | preserve newline answer surface | answer: fixed loss |
| surface-completion-space | surface_format | global | preserve space completion surface | completion: fixed loss |
| surface-completion-newline | surface_format | global | preserve newline completion surface | completion: fixed loss |
| suffix-ratio-fixed-l-a | training_corpus_ratio | global | increase suffix uptake density | fixed l loss fixed loss |
| suffix-ratio-fixed-l-b | training_corpus_ratio | global | increase suffix uptake density | fixed l fixed loss |
| suffix-ratio-fixed-lo-a | training_corpus_ratio | global | increase suffix uptake density | fixed lo loss fixed loss |
| suffix-ratio-fixed-lo-b | training_corpus_ratio | global | increase suffix uptake density | fixed lo fixed loss |
| verification-gate-note | verification_gate | global | keep replay gate explicit | sample success is not contract recovery replay fixed loss before promotion |
