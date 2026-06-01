# MiniGPT Required-Term Pair Contrast-Free Objective Corpus Contract

- Status: `pass`
- Decision: `contrast_free_objective_corpus_modes_ready`
- New modes: `3`
- Source prompts: `fixed= / loss=`
- Pair id removed: `True`

| Mode | Role | Pair id removed |
| --- | --- | --- |
| equals_surface_no_pair_id_fixed_retention_contrast_free_repair | separate branch rows without naming the opposite term | True |
| equals_surface_no_pair_id_fixed_retention_delimiter_span_repair | stop the target span with punctuation | True |
| equals_surface_no_pair_id_fixed_retention_context_switch_repair | separate fixed/loss contexts while preserving prompt surface | True |

## Validation

```text
python -m pytest tests\test_model_capability_required_term_pair_contrast_free_objective_corpus.py tests\test_model_capability_required_term_pair_coexistence_refresh.py -q -o cache_dir=runs\pytest-cache-v610-targeted
27 passed
```

## Next Action

Run real seed `3535` training for the three contrast-free objective modes.
