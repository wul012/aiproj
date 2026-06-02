# MiniGPT Required-Term Pair Minimal Prompt Corpus Contract

- Status: `pass`
- Decision: `minimal_prompt_equals_surface_corpus_contract_ready`
- Corpus mode: `minimal_prompt_equals_surface_objective`
- Source prompts: `['fixed=', 'loss=']`
- Model quality claim: `corpus_contract_only`

## Checks

| Check | Status | Actual | Detail |
| --- | --- | --- | --- |
| readiness_passed | pass | pass | readiness report must pass |
| objective_ready | pass | True | minimal prompt objective must be ready |
| corpus_mode_registered | pass | minimal_prompt_equals_surface_objective | recommended corpus mode must be registered |
| source_prompts_are_minimal | pass | ['fixed=', 'loss='] | source prompts must be fixed= and loss= |
| fixed_target_present | pass | True | corpus must contain fixed=fixed direct row |
| loss_target_present | pass | True | corpus must contain loss=loss direct row |
| fixed_prefix_present | pass | True | corpus must contain fixed prefix spans |
| loss_prefix_present | pass | True | corpus must contain loss prefix spans |
| no_contextual_anchor_patterns | pass | [] | corpus contract must avoid answer-bearing paired prompt anchors |
| no_pair_id | pass | False | minimal prompt corpus must not reintroduce numeric pair ids |

## Sample Lines

- `MiniGPT fixed/loss pair coexistence refresh corpus.`
- `The prompt before the colon selects the exact continuation term.`
- `fixed=f`
- `fixed=fi`
- `fixed=fix`
- `fixed=fixed`
- `prompt fixed= completion fixed`
- `minimal prompt fixed= target fixed`
- `after fixed= write fixed`
- `fixed= stops after fixed`
- `loss=l`
- `loss=lo`
- `loss=los`
- `loss=loss`
- `prompt loss= completion loss`
- `minimal prompt loss= target loss`
- `after loss= write loss`
- `loss= stops after loss`
- `fixed=f`
- `fixed=fi`

## Next Action

run a real tiny checkpoint with corpus_mode=minimal_prompt_equals_surface_objective
