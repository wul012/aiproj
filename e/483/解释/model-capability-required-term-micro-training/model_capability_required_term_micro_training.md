# MiniGPT Model Capability Required-Term Micro-Training

- Status: `pass`
- Decision: `required_term_micro_training_uptake_observed`
- Micro-training decision: `targeted_micro_training_partially_learned_required_terms`
- Examples: `20`
- Generations: `20`
- Continuation hits: `4`
- Hit rate: `0.2`
- Corpus: `e\483\解释\model-capability-required-term-micro-training\required_term_micro_corpus.txt` (`1442` lines)
- Checkpoint: `e\483\解释\model-capability-required-term-micro-training\micro-run\checkpoint.pt`

| Seed | Case | Term | Prompt | Continuation hit | Preview |
| ---: | --- | --- | --- | ---: | --- |
| 1337 | classification-risk-level | because | because: | 0 |  dadatat |
| 1337 | comparison-baseline | fixed | fixed: | 0 |  dadatat |
| 1337 | continuation-science | text | text: | 0 |  dtadata |
| 1337 | factual-val-loss | loss | loss: | 0 |  dadatat |
| 1337 | qa-training-loop | data | data: | 1 |  dadatat |
| 1337 | refusal-boundary | real | real: | 0 |  dadatat |
| 1337 | self-check-missing-data | data | data: | 1 |  dadatat |
| 1337 | structured-experiment-json | four | four: | 0 |  dadatat |
| 1337 | style-rewrite-concise | while | while: | 0 |  dhadata |
| 1337 | summary-evidence-chain | chain | chain: | 0 |  dadatat |
| 2026 | classification-risk-level | because | because: | 0 |  dadatat |
| 2026 | comparison-baseline | fixed | fixed: | 0 |  dadatat |
| 2026 | continuation-science | text | text: | 0 |  dtadata |
| 2026 | factual-val-loss | loss | loss: | 0 |  dadatat |
| 2026 | qa-training-loop | data | data: | 1 |  dadatat |
| 2026 | refusal-boundary | real | real: | 0 |  dadatat |
| 2026 | self-check-missing-data | data | data: | 1 |  dadatat |
| 2026 | structured-experiment-json | four | four: | 0 |  dadatat |
| 2026 | style-rewrite-concise | while | while: | 0 |  dhadata |
| 2026 | summary-evidence-chain | chain | chain: | 0 |  dadatat |

## Boundary

- Model quality claim: `targeted_micro_training_signal_only`
- Reason: A tiny model trained on explicit scaffold-to-term examples emitted required terms in continuation for at least one probe.
- Next action: repeat with a held-out required-term slice and compare whether the signal survives beyond copied scaffolds
