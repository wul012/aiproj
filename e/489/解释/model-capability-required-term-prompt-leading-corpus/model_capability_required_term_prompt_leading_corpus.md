# MiniGPT Model Capability Required-Term Prompt-Leading Corpus

- Status: `pass`
- Decision: `required_term_prompt_leading_corpus_candidate_ready`
- Prompt-leading corpus decision: `prompt_leading_corpus_candidate_ready`
- Prompt alignment ready: `True`
- Prompt-leading lines: `360`
- Previous prompt alignment: `False`
- Previous prompt-leading lines: `0`
- Term line spread: `0`
- Corpus: `e\489\解释\model-capability-required-term-prompt-leading-corpus\required_term_prompt_leading_corpus.txt`

| Case | Term | Prompt | Lines |
| --- | --- | --- | ---: |
| classification-risk-level | because | because: | 40 |
| comparison-baseline | fixed | fixed: | 40 |
| continuation-science | text | text: | 40 |
| factual-val-loss | loss | loss: | 40 |
| qa-training-loop | data | data: | 40 |
| refusal-boundary | real | real: | 40 |
| structured-experiment-json | four | four: | 40 |
| style-rewrite-concise | while | while: | 40 |
| summary-evidence-chain | chain | chain: | 40 |

## Boundary

- Model quality claim: `not_claimed`
- Reason: Every selected scaffold prompt now appears at the start of training rows while term exposure stays balanced.
- Next action: train a tiny checkpoint on this prompt-leading corpus and compare continuation uptake
