# MiniGPT Model Capability Required-Term One-Term Seed Stability

- Status: `pass`
- Decision: `required_term_one_term_seed_stability_observed`
- Seed-stability decision: `some_successful_terms_seed_stable`
- Source successful terms: `5`
- Selected terms: `5`
- Seeds: `3`
- Training pass count: `15`
- Checkpoints: `15`
- Term-seed hits: `14`
- Stable terms: `4`
- Partial terms: `1`

| Term | Source hit | Hit seeds | Missed seeds | Hit rate | Stable |
| --- | ---: | --- | --- | ---: | --- |
| fixed | 1 | 493, 1493, 2493 |  | 1.0 | True |
| text | 1 | 493, 2493 | 1493 | 0.6667 | False |
| loss | 1 | 493, 1493, 2493 |  | 1.0 | True |
| four | 1 | 493, 1493, 2493 |  | 1.0 | True |
| chain | 1 | 493, 1493, 2493 |  | 1.0 | True |

## Boundary

- Model quality claim: `one_term_seed_stable_capacity_signal_only`
- Reason: At least one v492 successful one-term case reproduced continuation uptake across all configured seeds.
- Next action: use stable one-term cases as a small curriculum before reintroducing multiple terms
