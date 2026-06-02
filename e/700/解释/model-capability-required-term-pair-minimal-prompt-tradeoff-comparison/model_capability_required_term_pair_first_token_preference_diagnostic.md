# MiniGPT Required-Term Pair First-Token Preference Diagnostic

- Status: `pass`
- Decision: `first_token_preference_tradeoff_confirmed`
- First-token conflict confirmed: `True`
- Mixed branch tradeoff confirmed: `True`
- Other-term start count: `4`

## Prompt Rows

| Source | Profile | Term | First | Vote | Hit | Continuation |
| --- | --- | --- | --- | --- | --- | --- |
| v696-fixed-dominant | default | fixed | f/f | fixed-start | True | fixed=fixed= |
| v696-fixed-dominant | suppress_newline_tokens | fixed | f/f | fixed-start | True | fixed=fixed= |
| v696-fixed-dominant | default | loss | f/l | fixed-start | False | fixed=fixed= |
| v696-fixed-dominant | suppress_newline_tokens | loss | f/l | fixed-start | False | fixed=fixed= |
| v699-loss-dominant | default | fixed | l/f | loss-start | False | losssssss= l |
| v699-loss-dominant | suppress_newline_tokens | fixed | l/f | loss-start | False | losssssss= l |
| v699-loss-dominant | default | loss | l/l | other | True |  losssssss=  |
| v699-loss-dominant | suppress_newline_tokens | loss | l/l | other | True |  losssssss=  |

## Boundary

- Model quality claim: `diagnostic_only`
- Reason: The same prompt surface flips between fixed-only and loss-only outcomes without a pair-full route.
- Next action: design a contrast-free objective that separates first-token choice from repeated term loops
