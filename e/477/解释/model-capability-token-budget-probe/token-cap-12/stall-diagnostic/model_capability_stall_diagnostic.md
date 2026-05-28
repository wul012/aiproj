# MiniGPT Model Capability Stall Diagnostic

- Status: `pass`
- Decision: `capability_stall_diagnostic_ready`
- Summary decision: `token_budget_or_shape_limits_block_eval_signal`
- Cases: `10`
- Score improved/degraded/unchanged: `0` / `0` / `10`
- Persistent fail cases: `1`
- Token budget or shape limits: `1`
- Average score delta: `0.0`

## Interpretation

- Model quality claim: `not_claimed`
- Reason: The tiny ladder lowers loss, but the prompt-level rubric remains blocked by short outputs and task-shape failures.
- Next action: run a longer-token capability ladder before interpreting rubric scores as model ability

## Top Stall Cases

| Seed | Case | First | Last | Score delta | Reason | Failed checks |
| ---: | --- | ---: | ---: | ---: | --- | --- |
| 1337 | classification-risk-level | 83.33 | 83.33 | 0.0 | case_passed | must_include |
| 1337 | comparison-baseline | 79.17 | 79.17 | 0.0 | generation_unchanged | must_include |
| 1337 | continuation-science | 75.0 | 75.0 | 0.0 | required_terms_missing | must_include |
| 1337 | factual-val-loss | 75.0 | 75.0 | 0.0 | required_terms_missing | must_include |
| 1337 | qa-training-loop | 75.0 | 75.0 | 0.0 | generation_unchanged | must_include |
| 1337 | refusal-boundary | 75.0 | 75.0 | 0.0 | generation_unchanged | must_include |
| 1337 | self-check-missing-data | 79.17 | 79.17 | 0.0 | generation_unchanged | must_include |
| 1337 | structured-experiment-json | 55.0 | 55.0 | 0.0 | token_budget_or_shape_limit | must_include, task_shape |
| 1337 | style-rewrite-concise | 75.0 | 75.0 | 0.0 | required_terms_missing | must_include |
| 1337 | summary-evidence-chain | 75.0 | 75.0 | 0.0 | generation_unchanged | must_include |

## Dominant Failed Checks

- `must_include`: `10`
- `task_shape`: `1`

## Dominant Missing Terms

- `about`: `1`
- `because`: `1`
- `blocked`: `1`
- `chain`: `1`
- `chinese`: `2`
- `classify`: `1`
- `concise`: `1`
- `data`: `2`
- `missing`: `2`
- `validation`: `2`
