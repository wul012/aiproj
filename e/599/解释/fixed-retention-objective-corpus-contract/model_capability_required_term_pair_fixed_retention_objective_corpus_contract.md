# MiniGPT Required-Term Pair Fixed-Retention Objective Corpus Contract

- Status: `pass`
- Decision: `fixed_retention_objective_corpus_modes_ready`
- Version: `v599.0.0`
- New mode count: `3`
- Source prompts: `fixed= / loss=`

## Modes

| Mode | Role | Pair id removed | Fixed retention bias | Loss branch visible |
| --- | --- | --- | --- | --- |
| equals_surface_no_pair_id_fixed_retention_balanced_repair | balanced fixed-retention | True | True | True |
| equals_surface_no_pair_id_fixed_retention_first_token_repair | fixed first-token retention | True | True | True |
| equals_surface_no_pair_id_fixed_retention_prompt_guard_repair | prompt surface guard | True | True | True |

## Boundary

This contract only proves the corpus modes are registered, prompt-compatible, and test-covered. It does not claim model improvement until real seed training is run.
