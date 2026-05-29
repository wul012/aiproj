# MiniGPT Model Capability Required-Term Balanced Corpus

- Status: `pass`
- Decision: `required_term_balanced_corpus_candidate_ready`
- Balanced corpus decision: `balanced_corpus_candidate_ready`
- Examples: `9`
- Source examples: `20`
- Unique line rate: `1.0`
- Legacy unique line rate: `0.133`
- Term line spread: `0`
- Corpus: `e\487\解释\model-capability-required-term-balanced-corpus\required_term_balanced_corpus.txt`
- Patterns: `direct_cue, spaced_cue, case_binding, instruction_binding, question_answer, contrastive_boundary`
- Selection strategy: `one representative row per unique required term`

| Case | Term | Lines | Prompt |
| --- | --- | ---: | --- |
| classification-risk-level | because | 48 | because: |
| comparison-baseline | fixed | 48 | fixed: |
| continuation-science | text | 48 | text: |
| factual-val-loss | loss | 48 | loss: |
| qa-training-loop | data | 48 | data: |
| refusal-boundary | real | 48 | real: |
| structured-experiment-json | four | 48 | four: |
| style-rewrite-concise | while | 48 | while: |
| summary-evidence-chain | chain | 48 | chain: |

## Boundary

- Model quality claim: `not_claimed`
- Reason: The candidate corpus keeps term exposure balanced while increasing line uniqueness versus the legacy repeated corpus.
- Next action: train a tiny checkpoint on this balanced corpus and rerun split/seed stability
