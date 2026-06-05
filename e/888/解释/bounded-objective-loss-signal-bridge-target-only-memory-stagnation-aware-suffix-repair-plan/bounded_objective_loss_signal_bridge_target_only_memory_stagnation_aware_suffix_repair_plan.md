# MiniGPT bounded objective loss signal bridge target-only memory stagnation-aware suffix repair plan

- Status: `pass`
- Decision: `bounded_objective_loss_signal_bridge_target_only_memory_stagnation_aware_suffix_repair_plan_ready`
- Action count: `5`
- Required actions: `5`
- No contract gain source: `True`
- Next step: `build_bounded_objective_loss_signal_bridge_target_only_memory_stagnation_aware_suffix_patch`

## Plan Actions

| Action | Category | Priority | Purpose | Implementation hint |
| --- | --- | --- | --- | --- |
| suffix-position-bridge | suffix_position | required | Add examples where loss immediately follows the fixed-l and fixed-lo fragments under the exact contract labels. | Generate paired snippets for `fixed l -> fixed loss`, `fixed lo -> fixed loss`, and direct `fixed loss` completions. |
| surface-format-normalization | surface_format | required | Preserve both space-prefixed and newline-prefixed continuations so formatting drift does not hide suffix progress. | Create parallel answer/completion examples for ` answer: fixed loss` and `answer:\nfixed loss` surfaces. |
| replay-prompt-boundary-lock | replay_prompt_boundary | required | Bind patch examples to the unchanged v836 prompts instead of relying on free-form sample prompts. | Use the canonical/minimal/completion contract prompts as literal prefixes in the next patch corpus. |
| suffix-ratio-increase | training_corpus_ratio | required | Raise suffix-uptake examples above surface carry-forward examples because the prior patch changed formatting without adding loss hits. | Target at least 2:1 suffix-uptake to surface-carry-forward examples, while keeping decoder anchors at zero. |
| contract-gated-training-stop | verification_gate | required | Keep training claims gated behind unchanged contract replay, since v885 sample success did not transfer. | Require a replay comparison before any promotion or holdout route; do not infer recovery from sample text. |
