# MiniGPT Required-Term Pair First-Token Preference Diagnostic

- Status: `pass`
- Decision: `first_token_preference_tradeoff_confirmed`
- First-token conflict confirmed: `True`
- Mixed branch tradeoff confirmed: `True`
- Other-term start count: `8`

## Prompt Rows

| Source | Profile | Term | First | Vote | Hit | Continuation |
| --- | --- | --- | --- | --- | --- | --- |
| v600-balanced | default | fixed | l/f | other | False |  losssssssss |
| v600-balanced | suppress_newline_tokens | fixed | l/f | other | False |  losssssssss |
| v600-balanced | default | loss | f/l | fixed-start | False | fixed\nfixed  |
| v600-balanced | suppress_newline_tokens | loss | f/l | fixed-start | True | fixed= losss |
| v601-first-token | default | fixed | f/f | fixed-start | True | fixed=fixed= |
| v601-first-token | suppress_newline_tokens | fixed | f/f | fixed-start | True | fixed=fixed= |
| v601-first-token | default | loss | f/l | fixed-start | False | fixed=fixed= |
| v601-first-token | suppress_newline_tokens | loss | f/l | fixed-start | False | fixed=fixed= |
| v602-prompt-guard | default | fixed | l/f | other | False |  loss\nlos\nlo |
| v602-prompt-guard | suppress_newline_tokens | fixed | l/f | other | False |  losssssssss |
| v602-prompt-guard | default | loss | l/l | other | True |  losss\nlos\nl |
| v602-prompt-guard | suppress_newline_tokens | loss | l/l | other | True |  losssssssss |
| v606-loss-rebalance | default | fixed | l/f | loss-start | False | lossssssssss |
| v606-loss-rebalance | suppress_newline_tokens | fixed | l/f | loss-start | False | lossssssssss |
| v606-loss-rebalance | default | loss | l/l | loss-start | True | lossssssssss |
| v606-loss-rebalance | suppress_newline_tokens | loss | l/l | loss-start | True | lossssssssss |
| v607-dual-cycle | default | fixed | f/f | fixed-start | True | fixed=fixed= |
| v607-dual-cycle | suppress_newline_tokens | fixed | f/f | fixed-start | True | fixed=fixed= |
| v607-dual-cycle | default | loss | f/l | fixed-start | False | fixed=los=fi |
| v607-dual-cycle | suppress_newline_tokens | loss | f/l | fixed-start | False | fixed=los=fi |

## Boundary

- Model quality claim: `diagnostic_only`
- Reason: The same prompt surface flips between fixed-only and loss-only outcomes without a pair-full route.
- Next action: design a contrast-free objective that separates first-token choice from repeated term loops
