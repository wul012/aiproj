# MiniGPT Required-Term Pair Minimal Prompt Branch-Bias Diagnostic

- Status: `pass`
- Decision: `minimal_prompt_branch_bias_fixed_absorbs_loss`
- Corpus mode: `minimal_prompt_equals_surface_objective`
- Dominant bias: `fixed`
- Model quality claim: `diagnostic_only`

## Rows

| Profile | Term | Prompt | Branch Vote | Hit | Continuation |
| --- | --- | --- | --- | --- | --- |
| default | fixed | fixed= | fixed-start | True | fixed=fixed= |
| suppress_newline_tokens | fixed | fixed= | fixed-start | True | fixed=fixed= |
| default | loss | loss= | fixed-start | False | fixed=fixed= |
| suppress_newline_tokens | loss | loss= | fixed-start | False | fixed=fixed= |

## Next Action

strengthen loss first-token and branch separation before rerunning the minimal-prompt training
