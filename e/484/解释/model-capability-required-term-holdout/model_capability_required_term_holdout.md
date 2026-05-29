# MiniGPT Model Capability Required-Term Holdout

- Status: `pass`
- Decision: `required_term_holdout_no_uptake`
- Holdout decision: `heldout_micro_training_no_required_term_uptake`
- Train examples: `12`
- Holdout examples: `8`
- Train hits: `0`
- Holdout hits: `0`
- Train terms: `because, chain, fixed, four, real, text`
- Holdout terms: `data, loss, while`
- Corpus: `e\484\解释\model-capability-required-term-holdout\required_term_holdout_corpus.txt`

| Split | Case | Term | Prompt | Hit | Preview |
| --- | --- | --- | --- | ---: | --- |
| train | classification-risk-level | because | because: | 0 | fousextt |
| train | comparison-baseline | fixed | fixed: | 0 | fousextt |
| train | continuation-science | text | text: | 0 | fousextt |
| train | refusal-boundary | real | real: | 0 | fousextt |
| train | structured-experiment-json | four | four: | 0 | fousextt |
| train | summary-evidence-chain | chain | chain: | 0 | fousextt |
| train | classification-risk-level | because | because: | 0 | fousextt |
| train | comparison-baseline | fixed | fixed: | 0 | fousextt |
| train | continuation-science | text | text: | 0 | fousextt |
| train | refusal-boundary | real | real: | 0 | fousextt |
| train | structured-experiment-json | four | four: | 0 | fousextt |
| train | summary-evidence-chain | chain | chain: | 0 | fousextt |
| holdout | factual-val-loss | loss | loss: | 0 | fousextt |
| holdout | qa-training-loop | data | data: | 0 | fousextt |
| holdout | self-check-missing-data | data | data: | 0 | fousextt |
| holdout | style-rewrite-concise | while | while: | 0 | fousextt |
| holdout | factual-val-loss | loss | loss: | 0 | fousextt |
| holdout | qa-training-loop | data | data: | 0 | fousextt |
| holdout | self-check-missing-data | data | data: | 0 | fousextt |
| holdout | style-rewrite-concise | while | while: | 0 | fousextt |

## Boundary

- Model quality claim: `not_claimed`
- Reason: Neither train nor held-out prompts produced required terms in continuation under this split.
- Next action: first reproduce train-slice uptake under a split before expanding benchmark scope
