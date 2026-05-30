# MiniGPT Required-Term Pair Prompt Separation Audit

- Status: `pass`
- Decision: `required_term_pair_prompt_separation_revision_needed`
- Audit decision: `prompt_separation_corpus_revision_needed`
- Prompt separation ready: `False`
- Direct other-term leaks: `960`
- Negative contrast leaks: `960`
- Corpus revision recommended: `True`

## Target Summary

| Target | Variant | Direct leak | Negative leak | Pair context | Ready |
| --- | --- | ---: | ---: | ---: | --- |
| 01-fixed-loss-baseline-repeat | baseline-repeat | 480 | 480 | 480 | False |
| 01-fixed-loss-longer-iters | longer-iters | 480 | 480 | 480 | False |

## Term Rows

| Target | Term | Prompt | Other-after-prompt | Example leak |
| --- | --- | --- | ---: | --- |
| 01-fixed-loss-baseline-repeat | fixed | fixed: | 240 | fixed:fixed not loss |
| 01-fixed-loss-baseline-repeat | loss | loss: | 240 | loss:loss not fixed |
| 01-fixed-loss-longer-iters | fixed | fixed: | 240 | fixed:fixed not loss |
| 01-fixed-loss-longer-iters | loss | loss: | 240 | loss:loss not fixed |

## Boundary

- Model quality claim: `not_claimed`
- Reason: The same scaffold prompt is followed by the other required term in corpus rows, so the pair corpus mixes target separation with contrast examples.
- Next action: build a contrast-free pair corpus variant before running another capacity or decoding sweep
