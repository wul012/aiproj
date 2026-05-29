# MiniGPT Model Capability Required-Term Uptake

- Status: `pass`
- Decision: `required_term_uptake_audit_ready`
- Uptake decision: `required_terms_never_generated`
- Generation observations: `212`
- Continuation hits: `0`
- Last-rung continuation hits: `0`
- Expected hits: `212`
- Prompt hits: `0`

| Seed | Case | Term | Max iters | Continuation hit | Expected hit | Preview |
| ---: | --- | --- | ---: | --- | --- | --- |
| 1337 | classification-risk-level | classify | 1 | False | True | 每\n每研工少评据两化据否 |
| 1337 | classification-risk-level | classify | 4 | False | True | 每\n每研工少评据两v据否 |
| 1337 | classification-risk-level | blocked | 1 | False | True | 每\n每研工少评据两化据否 |
| 1337 | classification-risk-level | blocked | 4 | False | True | 每\n每研工少评据两v据否 |
| 1337 | classification-risk-level | because | 1 | False | True | 每\n每研工少评据两化据否 |
| 1337 | classification-risk-level | because | 4 | False | True | 每\n每研工少评据两v据否 |
| 1337 | classification-risk-level | missing | 1 | False | True | 每\n每研工少评据两化据否 |
| 1337 | classification-risk-level | missing | 4 | False | True | 每\n每研工少评据两v据否 |
| 1337 | comparison-baseline | fixed | 1 | False | True | 方少s固工四一u少格径断 |
| 1337 | comparison-baseline | fixed | 4 | False | True | 方少s固工四一u少格径断 |
| 1337 | comparison-baseline | sampling | 1 | False | True | 方少s固工四一u少格径断 |
| 1337 | comparison-baseline | sampling | 4 | False | True | 方少s固工四一u少格径断 |
| 1337 | comparison-baseline | seeds | 1 | False | True | 方少s固工四一u少格径断 |
| 1337 | comparison-baseline | seeds | 4 | False | True | 方少s固工四一u少格径断 |
| 1337 | comparison-baseline | reduce | 1 | False | True | 方少s固工四一u少格径断 |
| 1337 | comparison-baseline | reduce | 4 | False | True | 方少s固工四一u少格径断 |
| 1337 | comparison-baseline | confounding | 1 | False | True | 方少s固工四一u少格径断 |
| 1337 | comparison-baseline | confounding | 4 | False | True | 方少s固工四一u少格径断 |
| 1337 | continuation-science | chinese | 1 | False | True | e四研少好？格或少四少. |
| 1337 | continuation-science | chinese | 4 | False | True | e四研少好？格或少四s存 |
| 1337 | continuation-science | text | 1 | False | True | e四研少好？格或少四少. |
| 1337 | continuation-science | text | 4 | False | True | e四研少好？格或少四s存 |
| 1337 | continuation-science | about | 1 | False | True | e四研少好？格或少四少. |
| 1337 | continuation-science | about | 4 | False | True | e四研少好？格或少四s存 |
| 1337 | continuation-science | scientific | 1 | False | True | e四研少好？格或少四少. |
| 1337 | continuation-science | scientific | 4 | False | True | e四研少好？格或少四s存 |
| 1337 | continuation-science | research | 1 | False | True | e四研少好？格或少四少. |
| 1337 | continuation-science | research | 4 | False | True | e四研少好？格或少四s存 |
| 1337 | factual-val-loss | statement | 1 | False | True | u成u指？.泛否据变更每 |
| 1337 | factual-val-loss | statement | 4 | False | True | u成u指？这泛否据变总每 |

## Boundary

- Model quality claim: `not_claimed`
- Reason: Archived suite outputs never place the required terms into continuations, even though those terms are present in expected behavior and corpus material.
- Next action: run a targeted decoding/training probe with explicit required-term scaffolds before increasing benchmark scope
