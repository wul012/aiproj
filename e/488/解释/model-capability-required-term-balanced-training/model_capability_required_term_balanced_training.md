# MiniGPT Model Capability Required-Term Balanced Training

- Status: `pass`
- Decision: `required_term_balanced_training_completed_without_uptake`
- Balanced training decision: `balanced_training_completed_without_uptake`
- Terms: `9`
- Generations: `9`
- Continuation hits: `0`
- Hit rate: `0.0`
- Prompt alignment ready: `False`
- Prompt-leading lines: `0`
- Source corpus: `e\487\解释\model-capability-required-term-balanced-corpus\required_term_balanced_corpus.txt`
- Checkpoint: `e\488\解释\model-capability-required-term-balanced-training\balanced-run\checkpoint.pt`

| Case | Term | Prompt | Continuation hit | Preview |
| --- | --- | --- | ---: | --- |
| classification-risk-level | because | because: | 0 | \|pate=07\|pat |
| comparison-baseline | fixed | fixed: | 0 | \|pate=07\|pat |
| continuation-science | text | text: | 0 | \|pate=07\|pat |
| factual-val-loss | loss | loss: | 0 | \|pate=07\|pat |
| qa-training-loop | data | data: | 0 | \|pate=07\|pat |
| refusal-boundary | real | real: | 0 | \|pate=07\|pat |
| structured-experiment-json | four | four: | 0 | \|pate=07\|pat |
| style-rewrite-concise | while | while: | 0 | \|pate=07\|pat |
| summary-evidence-chain | chain | chain: | 0 | \|pate=07\|pat |

## Boundary

- Model quality claim: `not_claimed`
- Reason: The balanced-corpus training run completed, but short continuations still did not include required terms.
- Next action: rebuild the balanced corpus with prompt-leading scaffold-to-term rows before increasing training budget
