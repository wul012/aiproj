# MiniGPT Required-Term Pair Loss-Branch Objective Corpus Contract

- Status: `pass`
- Decision: `loss_branch_objective_corpus_modes_ready`
- Version: `v589.0.0`

## New Corpus Modes

| Mode | Role |
| --- | --- |
| `equals_surface_no_pair_id_loss_branch_targeted_repair` | Weights the missed `loss` branch while keeping `fixed` as a clean target. |
| `equals_surface_no_pair_id_loss_branch_dual_anchor_repair` | Places `loss=loss` and `fixed=fixed` in the same clean anchor records. |
| `equals_surface_no_pair_id_loss_branch_micro_span_repair` | Adds short `loss=` prefix spans so the first loss token is visible. |

## Validation

```text
python -m py_compile src\minigpt\model_capability_required_term_pair_loss_branch_objective_corpus.py src\minigpt\model_capability_required_term_pair_coexistence_corpus.py tests\test_model_capability_required_term_pair_coexistence_refresh.py
python -m pytest tests\test_model_capability_required_term_pair_coexistence_refresh.py -q -o cache_dir=runs\pytest-cache-v589
23 passed in 0.35s
git diff --check
pass
```

## Boundary

v589 only defines and verifies the objective corpus contract. It does not claim model improvement until v590-v592 run real tiny training checkpoints.
