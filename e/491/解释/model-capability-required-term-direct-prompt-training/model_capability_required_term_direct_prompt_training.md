# MiniGPT Model Capability Required-Term Direct Prompt Training

- Status: `pass`
- Decision: `required_term_direct_prompt_training_completed_without_uptake`
- Direct prompt training decision: `direct_prompt_training_completed_without_uptake`
- Terms: `9`
- Generations: `9`
- Continuation hits: `0`
- Previous continuation hits: `0`
- Continuation hit delta: `0`
- Direct prompt lines: `2880`
- Source corpus: `e\491\解释\model-capability-required-term-direct-prompt-training\required_term_direct_prompt_corpus.txt`
- Checkpoint: `e\491\解释\model-capability-required-term-direct-prompt-training\direct-prompt-run\checkpoint.pt`

| Case | Term | Prompt | Current hits | Delta | Preview |
| --- | --- | --- | ---: | ---: | --- |
| classification-risk-level | because | because: | 0 | 0 |  fixecauseca |
| comparison-baseline | fixed | fixed: | 0 | 0 |  fixecauseca |
| continuation-science | text | text: | 0 | 0 |  fixecauseca |
| factual-val-loss | loss | loss: | 0 | 0 |  fixecauseca |
| qa-training-loop | data | data: | 0 | 0 |  fixecauseca |
| refusal-boundary | real | real: | 0 | 0 |  fixecauseca |
| structured-experiment-json | four | four: | 0 | 0 |  fixecauseca |
| style-rewrite-concise | while | while: | 0 | 0 |  fixecauseca |
| summary-evidence-chain | chain | chain: | 0 | 0 |  fixecauseca |

## Boundary

- Model quality claim: `not_claimed`
- Reason: The direct prompt training run completed, but short continuations still did not include required terms.
- Next action: increase repeat or max_iters further, or train one term at a time to isolate capacity limits
