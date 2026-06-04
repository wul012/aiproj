# MiniGPT bounded objective loss signal bridge single-line surface patch

- Status: `pass`
- Decision: `bounded_objective_loss_signal_bridge_single_line_surface_patch_ready`
- Patch examples: `14`
- Single-line cases: `6`
- Direct-label examples: `6`
- Completion surfaces: `2`
- Claim: `single_line_surface_patch_only`

## Patch Examples

| Example | Kind | Text | Source |
| --- | --- | --- | --- |
| canonical_direct_completion-single-line-case-a | single_line_case_surface | Answer with exactly two tokens: fixed loss answer: fixed loss | canonical_direct_completion |
| canonical_direct_completion-single-line-case-b | single_line_case_surface | Answer with exactly two tokens: fixed loss answer: fixed loss | canonical_direct_completion |
| minimal_direct_completion-single-line-case-a | single_line_case_surface | Answer with exactly two words: fixed loss answer: fixed loss | minimal_direct_completion |
| minimal_direct_completion-single-line-case-b | single_line_case_surface | Answer with exactly two words: fixed loss answer: fixed loss | minimal_direct_completion |
| completion_label_surface-single-line-case-a | single_line_case_surface | Complete with exactly two tokens: fixed loss completion: fixed loss | completion_label_surface |
| completion_label_surface-single-line-case-b | single_line_case_surface | Complete with exactly two tokens: fixed loss completion: fixed loss | completion_label_surface |
| answer-label-direct-a | direct_label_surface | answer: fixed loss | global |
| answer-label-direct-b | direct_label_surface | answer: fixed loss | global |
| completion-label-direct-a | direct_label_surface | completion: fixed loss | global |
| completion-label-direct-b | direct_label_surface | completion: fixed loss | global |
| target-label-direct-a | direct_label_surface | target: fixed loss | global |
| target-label-direct-b | direct_label_surface | target: fixed loss | global |
| fixed-loss-plain-a | completion_surface_single_line | fixed loss | global |
| fixed-loss-plain-b | completion_surface_single_line | fixed loss | global |
