# MiniGPT Model Capability Stall Diagnostic

- Status: `pass`
- Decision: `capability_stall_diagnostic_ready`
- Summary decision: `token_budget_or_shape_limits_block_eval_signal`
- Cases: `10`
- Score improved/degraded/unchanged: `0` / `0` / `10`
- Persistent fail cases: `10`
- Token budget or shape limits: `10`
- Average score delta: `0.0`

## Interpretation

- Model quality claim: `not_claimed`
- Reason: The tiny ladder lowers loss, but the prompt-level rubric remains blocked by short outputs and task-shape failures.
- Next action: run a longer-token capability ladder before interpreting rubric scores as model ability

## Top Stall Cases

| Seed | Case | First | Last | Score delta | Reason | Failed checks |
| ---: | --- | ---: | ---: | ---: | --- | --- |
| 2026 | classification-risk-level | 43.33 | 43.33 | 0.0 | token_budget_or_shape_limit | length_bounds, must_include, task_shape |
| 2026 | comparison-baseline | 39.17 | 39.17 | 0.0 | token_budget_or_shape_limit | length_bounds, must_include, task_shape |
| 2026 | continuation-science | 35.0 | 35.0 | 0.0 | token_budget_or_shape_limit | length_bounds, must_include, task_shape |
| 2026 | factual-val-loss | 35.0 | 35.0 | 0.0 | token_budget_or_shape_limit | length_bounds, must_include, task_shape |
| 2026 | qa-training-loop | 35.0 | 35.0 | 0.0 | token_budget_or_shape_limit | length_bounds, must_include, task_shape |
| 2026 | refusal-boundary | 35.0 | 35.0 | 0.0 | token_budget_or_shape_limit | length_bounds, must_include, task_shape |
| 2026 | self-check-missing-data | 39.17 | 39.17 | 0.0 | token_budget_or_shape_limit | length_bounds, must_include, task_shape |
| 2026 | structured-experiment-json | 55.0 | 55.0 | 0.0 | token_budget_or_shape_limit | must_include, task_shape |
| 2026 | style-rewrite-concise | 35.0 | 35.0 | 0.0 | token_budget_or_shape_limit | length_bounds, must_include, task_shape |
| 2026 | summary-evidence-chain | 35.0 | 35.0 | 0.0 | token_budget_or_shape_limit | length_bounds, must_include, task_shape |

## Dominant Failed Checks

- `length_bounds`: `9`
- `must_include`: `10`
- `task_shape`: `10`

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
