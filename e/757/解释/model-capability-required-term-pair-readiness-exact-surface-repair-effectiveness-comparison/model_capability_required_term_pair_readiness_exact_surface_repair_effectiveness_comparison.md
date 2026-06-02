# MiniGPT Exact-Surface Repair Effectiveness Comparison

- Status: `pass`
- Decision: `pair_readiness_exact_surface_repair_ineffective_stop_route`

## Comparison Rows

| Spec | Prompt | Before full | After full | Before hits | After hits | Delta |
| --- | --- | --- | --- | --- | --- | --- |
| arrow-heldout-pair | fixed -> \| loss -> | True | True | 2 | 2 | 0 |
| exact-heldout-pair | fixed=\|loss= | False | False | 1 | 1 | 0 |
| spaced-heldout-pair | fixed= \| loss= | False | False | 1 | 1 | 0 |
