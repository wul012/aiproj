# MiniGPT bounded objective loss signal bridge target-only memory loss-token probability probe

- Status: `pass`
- Decision: `bounded_objective_loss_signal_bridge_target_only_memory_loss_token_probability_probe_loss_suffix_top1_but_decode_blocked`
- Target top-1 rate: `1.0`
- Target top-k rate: `1.0`
- Min target probability: `0.9280321598052979`
- Mean target probability: `0.952898469236162`
- Max target rank: `1`
- Low-probability steps: `0`
- Next step: `inspect_decoding_temperature_or_stop_condition_for_loss_suffix`

## Probe Steps

| Case | Step | Target | Probability | Rank | Top token | State |
| --- | --- | --- | --- | --- | --- | --- |
| canonical_direct_completion | 0 | o | 0.9545234441757202 | 1 | o | target_top1 |
| canonical_direct_completion | 1 | s | 0.9480579495429993 | 1 | s | target_top1 |
| canonical_direct_completion | 2 | s | 0.965534508228302 | 1 | s | target_top1 |
| minimal_direct_completion | 0 | o | 0.9513438940048218 | 1 | o | target_top1 |
| minimal_direct_completion | 1 | s | 0.9547762870788574 | 1 | s | target_top1 |
| minimal_direct_completion | 2 | s | 0.9617397785186768 | 1 | s | target_top1 |
| completion_label_surface | 0 | o | 0.9280321598052979 | 1 | o | target_top1 |
| completion_label_surface | 1 | s | 0.9444912672042847 | 1 | s | target_top1 |
| completion_label_surface | 2 | s | 0.9675869345664978 | 1 | s | target_top1 |
