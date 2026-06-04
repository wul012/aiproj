# MiniGPT model capability route promotion bounded objective unassisted repair curriculum revision

- Status: `pass`
- Decision: `model_capability_route_promotion_bounded_objective_unassisted_repair_curriculum_revision_ready`
- Ready: `True`
- Revision items: `7`
- Acceptance gates: `4`
- Decoder anchors allowed: `False`

## Revision Items

| Item | Priority | Stage | Anchor | Action |
| --- | --- | --- | --- | --- |
| output_position_anchor_examples | high | seed_revision | False | Add examples where the answer appears immediately after the final answer marker, with no explanatory tokens before fixed loss. |
| neutral_prompt_exact_completion_repetition | high | seed_revision | False | Repeat neutral prompts with the exact two-token completion so target terms are learned without appearing in the prompt. |
| fragment_contrast_examples | medium | seed_revision | False | Add positive correction surfaces for observed fragments such as los, while keeping the training target as fixed loss. |
| short_decoding_profile_probe | medium | replay_revision | False | After training, replay with short deterministic decoding before trying larger sampling changes. |
| unchanged_contract_holdout | high | holdout | False | Keep the v836 objective contract unchanged so the revised seed cannot move the goalposts. |
| prompt_surface_balance | medium | seed_revision | False | Balance contract prompt surfaces and neutral prompt surfaces so one prompt form does not dominate. |
| near_miss_fragment_tracking | medium | diagnostic | False | Track los/wixed-style fragments in the next replay comparison as diagnostic-only evidence. |

## Acceptance Gates

| Gate | Required | Detail |
| --- | --- | --- |
| seed_revision_ready | True | revised seed must pass and keep decoder_anchor_example_count=0 |
| training_artifacts_ready | True | revised training run must produce checkpoint, tokenizer, metrics, manifest, sample, and prepared corpus |
| unassisted_replay_improves | True | next replay must improve any_hit_case_count or pass_rate before further promotion review |
| unchanged_contract_preserved | True | v836 objective contract cases must remain unchanged |
