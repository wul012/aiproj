# MiniGPT Pair-Readiness Structured-Template Contract

- Status: `pass`
- Decision: `pair_readiness_structured_template_contract_ready`
- Template family: `prompt_answer_structured_direct_terms`

## Training Rows

- `task: complete required term | prompt: fixed= | answer: fixed`
- `task: complete required term | prompt: loss= | answer: loss`
- `case=fixed | prompt=fixed= | expected=fixed | answer=fixed`
- `case=loss | prompt=loss= | expected=loss | answer=loss`
- `fixed direct template -> fixed`
- `loss direct template -> loss`
- `fixed route target term is fixed`
- `loss route target term is loss`
- `when prompt begins fixed= complete fixed`
- `when prompt begins loss= complete loss`
- `required term fixed stays on fixed branch`
- `required term loss stays on loss branch`
- `fixed branch answer uses fixed and avoids loss`
- `loss branch answer uses loss and avoids fixed`

## Checks

| Check | Status | Actual | Detail |
| --- | --- | --- | --- |
| source_comparison_passed | pass | pass | source comparison must pass |
| source_comparison_decision | pass | pair_readiness_loss_retention_patch_regressed | structured template route follows only the closed loss-retention regression branch |
| prior_route_regressed | pass | True | source must confirm the prior repair regressed |
| prior_default_delta_negative | pass | -1 | source default-hit delta must be negative |
| training_rows_present | pass | 14 | structured template rows must be substantial enough to materialize |
| fixed_rows_present | pass | 8 | fixed route must have repeated structured anchors |
| loss_rows_present | pass | 8 | loss route must have repeated structured anchors |
| evaluation_probes_present | pass | 3 | fixed, loss, and pair probes must be preserved |
| no_exact_eval_row_overlap | pass | [] | exact eval prompts must not be training rows |
| heldout_pair_absent | pass | False | heldout pair probe must stay out of training rows |
