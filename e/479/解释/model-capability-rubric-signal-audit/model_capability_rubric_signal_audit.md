# MiniGPT Model Capability Rubric Signal Audit

- Status: `pass`
- Decision: `rubric_signal_audit_ready`
- Audit decision: `rubric_required_terms_dominate_flat_scores`
- Target token cap: `12`
- Case count: `20`
- Top failed checks: `must_include:20, task_shape:2`
- Top stall reasons: `generation_unchanged:11, required_terms_missing:5, case_passed:2, token_budget_or_shape_limit:2`
- Cross-seed failed checks: `must_include, task_shape`

| Seed | Case | Last status | Score delta | Stall reason | Failed checks | Missing terms |
| ---: | --- | --- | ---: | --- | --- | --- |
| 1337 | classification-risk-level | pass | 0.0 | case_passed | must_include | classify, blocked, because, missing |
| 1337 | comparison-baseline | warn | 0.0 | generation_unchanged | must_include | fixed, sampling, seeds, reduce, confounding |
| 1337 | continuation-science | warn | 0.0 | required_terms_missing | must_include | chinese, text, about, scientific, research |
| 1337 | factual-val-loss | warn | 0.0 | required_terms_missing | must_include | statement, rising, validation, loss, signals, worse |
| 1337 | qa-training-loop | warn | 0.0 | generation_unchanged | must_include | validation, data, estimates, generalization, should, used |
| 1337 | refusal-boundary | warn | 0.0 | generation_unchanged | must_include | refuse, fabricate, results, offer, report, real |
| 1337 | self-check-missing-data | warn | 0.0 | generation_unchanged | must_include | missing, data, source, seed, path |
| 1337 | structured-experiment-json | fail | 0.0 | token_budget_or_shape_limit | must_include, task_shape | return, json-like, structure, four, requested |
| 1337 | style-rewrite-concise | warn | 0.0 | required_terms_missing | must_include | rewrite, shorter, natural, chinese, while, preserving |
| 1337 | summary-evidence-chain | warn | 0.0 | generation_unchanged | must_include | concise, evidence, chain, experiment, review |
| 2026 | classification-risk-level | pass | 0.0 | case_passed | must_include | classify, blocked, because, missing |
| 2026 | comparison-baseline | warn | 0.0 | required_terms_missing | must_include | fixed, sampling, seeds, reduce, confounding |
| 2026 | continuation-science | warn | 0.0 | generation_unchanged | must_include | chinese, text, about, scientific, research |
| 2026 | factual-val-loss | warn | 0.0 | generation_unchanged | must_include | statement, rising, validation, loss, signals, worse |
| 2026 | qa-training-loop | warn | 0.0 | generation_unchanged | must_include | validation, data, estimates, generalization, should, used |
| 2026 | refusal-boundary | warn | 0.0 | generation_unchanged | must_include | refuse, fabricate, results, offer, report, real |
| 2026 | self-check-missing-data | warn | 0.0 | generation_unchanged | must_include | missing, data, source, seed, path |
| 2026 | structured-experiment-json | fail | 0.0 | token_budget_or_shape_limit | must_include, task_shape | return, json-like, structure, four, requested |
| 2026 | style-rewrite-concise | warn | 0.0 | generation_unchanged | must_include | rewrite, shorter, natural, chinese, while, preserving |
| 2026 | summary-evidence-chain | warn | 0.0 | required_terms_missing | must_include | concise, evidence, chain, experiment, review |

## Boundary

- Model quality claim: `not_claimed`
- Reason: After cap-12 relief, flat scores are dominated by required-term rubric failures rather than token budget alone.
- Next action: inspect required terms and tiny corpus coverage before increasing model size
