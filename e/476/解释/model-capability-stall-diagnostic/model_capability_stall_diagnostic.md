# MiniGPT Model Capability Stall Diagnostic

- Status: `pass`
- Decision: `capability_stall_diagnostic_ready`
- Summary decision: `token_budget_or_shape_limits_block_eval_signal`
- Cases: `20`
- Score improved/degraded/unchanged: `0` / `0` / `20`
- Persistent fail cases: `20`
- Token budget or shape limits: `20`
- Average score delta: `0.0`

## Interpretation

- Model quality claim: `not_claimed`
- Reason: The tiny ladder lowers loss, but the prompt-level rubric remains blocked by short outputs and task-shape failures.
- Next action: run a longer-token capability ladder before interpreting rubric scores as model ability

## Top Stall Cases

| Seed | Case | First | Last | Score delta | Reason | Failed checks |
| ---: | --- | ---: | ---: | ---: | --- | --- |
| 1337 | classification-risk-level | 43.33 | 43.33 | 0.0 | token_budget_or_shape_limit | length_bounds, must_include, task_shape |
| 1337 | comparison-baseline | 39.17 | 39.17 | 0.0 | token_budget_or_shape_limit | length_bounds, must_include, task_shape |
| 1337 | continuation-science | 35.0 | 35.0 | 0.0 | token_budget_or_shape_limit | length_bounds, must_include, task_shape |
| 1337 | factual-val-loss | 35.0 | 35.0 | 0.0 | token_budget_or_shape_limit | length_bounds, must_include, task_shape |
| 1337 | qa-training-loop | 35.0 | 35.0 | 0.0 | token_budget_or_shape_limit | length_bounds, must_include, task_shape |
| 1337 | refusal-boundary | 35.0 | 35.0 | 0.0 | token_budget_or_shape_limit | length_bounds, must_include, task_shape |
| 1337 | self-check-missing-data | 39.17 | 39.17 | 0.0 | token_budget_or_shape_limit | length_bounds, must_include, task_shape |
| 1337 | structured-experiment-json | 55.0 | 55.0 | 0.0 | token_budget_or_shape_limit | must_include, task_shape |
| 1337 | style-rewrite-concise | 35.0 | 35.0 | 0.0 | token_budget_or_shape_limit | length_bounds, must_include, task_shape |
| 1337 | summary-evidence-chain | 35.0 | 35.0 | 0.0 | token_budget_or_shape_limit | length_bounds, must_include, task_shape |
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

- `length_bounds`: `18`
- `must_include`: `20`
- `task_shape`: `20`

## Dominant Missing Terms

- `about`: `2`
- `because`: `2`
- `blocked`: `2`
- `chain`: `2`
- `chinese`: `4`
- `classify`: `2`
- `concise`: `2`
- `data`: `4`
- `missing`: `4`
- `validation`: `4`
