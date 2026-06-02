# MiniGPT Pair-Readiness Heldout Failure Diagnostic

- Status: `pass`
- Decision: `pair_readiness_loss_prompt_absorbed_by_fixed`

## Analysis Rows

| Profile | Term | Hit | Pollution | Generated |
| --- | --- | --- | --- | --- |
| default | fixed | True | expected-fixed | fixed=fixed=fixed= |
| suppress_newline_tokens | fixed | True | expected-fixed | fixed=fixed=fixed= |
| default | loss | False | loss-prompt-fixed-pollution | loss=fixed=fixed= |
| suppress_newline_tokens | loss | False | loss-prompt-fixed-pollution | loss=fixed=fixed= |
