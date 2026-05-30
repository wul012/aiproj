# MiniGPT Required-Term Pair Contrast-Free Training

- Status: `pass`
- Decision: `required_term_pair_contrast_free_training_partial`
- Training decision: `contrast_free_training_partial_only`
- Source audit: `prompt_separation_corpus_revision_needed`
- Selected pairs: `1`
- Variants: `3`
- Training pass count: `3`
- Full-hit variants: `0`
- Contrast-free full hit observed: `False`

## Variant Results

| Pair | Variant | Hits | Missed | Hit rate | Full hit |
| --- | --- | --- | --- | ---: | --- |
| 01-fixed-loss | contrast-baseline | fixed | loss | 0.5 | False |
| 01-fixed-loss | contrast-longer | fixed | loss | 0.5 | False |
| 01-fixed-loss | contrast-denser | fixed | loss | 0.5 | False |

## Pair Summary

| Pair | Full-hit variants | Partial variants | Best variant | Best hit count |
| --- | --- | --- | --- | ---: |
| 01-fixed-loss |  | contrast-baseline, contrast-longer, contrast-denser | contrast-longer | 1 |

## Boundary

- Model quality claim: `contrast_free_pair_partial_signal_only`
- Reason: The contrast-free corpus removed direct leakage, but the tiny pair checkpoint still only preserved part of the pair.
- Next action: inspect contrast-free generations and consider seed stability before adding more corpus templates
