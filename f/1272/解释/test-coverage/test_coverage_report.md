# MiniGPT test coverage report

- Generated: `2026-07-10T02:02:45Z`
- Decision: `continue_with_coverage_gate`
- Line coverage: `91.06`
- Covered lines: `90861/99778`
- Threshold enabled: `True`
- Fail under: `88.98`
- Coverage gap: `0.0`

## Lowest Coverage Files

| File | Coverage | Covered | Statements | Missing |
| --- | ---: | ---: | ---: | ---: |
| src/minigpt/model_capability_required_term_prompt_leading_training.py | 16.77 | 26 | 155 | 129 |
| src/minigpt/model_capability_required_term_prompt_leading_corpus.py | 17.26 | 29 | 168 | 139 |
| src/minigpt/model_capability_required_term_balanced_corpus.py | 17.9 | 29 | 162 | 133 |
| src/minigpt/model_capability_required_term_split_seed_stability.py | 18.06 | 26 | 144 | 118 |
| src/minigpt/model_capability_required_term_one_term_seed_stability.py | 18.18 | 30 | 165 | 135 |
| src/minigpt/model_capability_required_term_direct_prompt_training.py | 18.34 | 31 | 169 | 138 |
| src/minigpt/model_capability_required_term_coverage.py | 18.44 | 33 | 179 | 146 |
| src/minigpt/grok_trajectory_phases_v1181.py | 18.75 | 30 | 160 | 130 |
| src/minigpt/model_capability_required_term_holdout.py | 18.79 | 28 | 149 | 121 |
| src/minigpt/model_capability_required_term_balanced_training.py | 19.08 | 25 | 131 | 106 |
| src/minigpt/model_capability_stall_diagnostic.py | 19.14 | 31 | 162 | 131 |
| src/minigpt/model_capability_rubric_signal_audit.py | 19.42 | 27 | 139 | 112 |

## Recommendations

- Coverage 91.06% meets the configured fail-under gate of 88.98%.
- Review the lowest-coverage files first; add focused tests before raising any threshold.
