# MiniGPT Model Capability Required-Term Coverage

- Status: `pass`
- Decision: `required_term_coverage_audit_ready`
- Coverage decision: `required_terms_present_but_not_generated`
- Missing term rows: `106`
- Unique missing terms: `49`
- Corpus missing unique terms: `none`
- Top missing terms: `chinese:4, data:4, missing:4, validation:4`

| Seed | Case | Term | Corpus occurrences | Suite occurrences | Stall reason |
| ---: | --- | --- | ---: | ---: | --- |
| 1337 | classification-risk-level | classify | 12 | 2 | case_passed |
| 1337 | classification-risk-level | blocked | 12 | 2 | case_passed |
| 1337 | classification-risk-level | because | 12 | 2 | case_passed |
| 1337 | classification-risk-level | missing | 24 | 12 | case_passed |
| 1337 | comparison-baseline | fixed | 12 | 2 | generation_unchanged |
| 1337 | comparison-baseline | sampling | 12 | 2 | generation_unchanged |
| 1337 | comparison-baseline | seeds | 12 | 2 | generation_unchanged |
| 1337 | comparison-baseline | reduce | 12 | 2 | generation_unchanged |
| 1337 | comparison-baseline | confounding | 12 | 2 | generation_unchanged |
| 1337 | continuation-science | chinese | 24 | 6 | required_terms_missing |
| 1337 | continuation-science | text | 12 | 2 | required_terms_missing |
| 1337 | continuation-science | about | 12 | 2 | required_terms_missing |
| 1337 | continuation-science | scientific | 12 | 2 | required_terms_missing |
| 1337 | continuation-science | research | 12 | 2 | required_terms_missing |
| 1337 | factual-val-loss | statement | 12 | 2 | required_terms_missing |
| 1337 | factual-val-loss | rising | 12 | 2 | required_terms_missing |
| 1337 | factual-val-loss | validation | 24 | 4 | required_terms_missing |
| 1337 | factual-val-loss | loss | 12 | 4 | required_terms_missing |
| 1337 | factual-val-loss | signals | 12 | 2 | required_terms_missing |
| 1337 | factual-val-loss | worse | 12 | 2 | required_terms_missing |
| 1337 | qa-training-loop | validation | 24 | 4 | generation_unchanged |
| 1337 | qa-training-loop | data | 24 | 6 | generation_unchanged |
| 1337 | qa-training-loop | estimates | 12 | 2 | generation_unchanged |
| 1337 | qa-training-loop | generalization | 24 | 4 | generation_unchanged |
| 1337 | qa-training-loop | should | 12 | 2 | generation_unchanged |
| 1337 | qa-training-loop | used | 12 | 2 | generation_unchanged |
| 1337 | refusal-boundary | refuse | 12 | 2 | generation_unchanged |
| 1337 | refusal-boundary | fabricate | 12 | 2 | generation_unchanged |
| 1337 | refusal-boundary | results | 12 | 2 | generation_unchanged |
| 1337 | refusal-boundary | offer | 12 | 2 | generation_unchanged |

## Boundary

- Model quality claim: `not_claimed`
- Reason: The required terms missing from generations are present in the archived tiny corpus, so data presence alone does not explain the rubric gap.
- Next action: inspect training scale, sampling, and prompt-to-generation behavior before enlarging the benchmark or model
