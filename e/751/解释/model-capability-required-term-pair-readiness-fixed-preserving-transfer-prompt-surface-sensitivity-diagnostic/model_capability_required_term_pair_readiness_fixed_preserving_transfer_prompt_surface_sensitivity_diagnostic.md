# MiniGPT Prompt-Surface Sensitivity Diagnostic

- Status: `pass`
- Decision: `pair_readiness_fixed_preserving_transfer_prompt_surface_sensitivity_found`

## Surface Rows

| Spec | Prompt | Required | Pair-full | Hits | Diagnosis |
| --- | --- | --- | --- | --- | --- |
| exact-heldout-pair | fixed=\|loss= | True | False | 1/1 | required_surface_missed |
| spaced-heldout-pair | fixed= \| loss= | False | False | 1/1 | optional_surface_missed |
| arrow-heldout-pair | fixed -> \| loss -> | False | True | 2/2 | pair_full_surface |
