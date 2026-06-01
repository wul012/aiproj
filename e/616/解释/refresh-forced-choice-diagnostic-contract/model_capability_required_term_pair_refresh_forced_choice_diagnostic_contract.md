# MiniGPT Required-Term Pair Refresh Forced-Choice Diagnostic Contract

- Status: `pass`
- Decision: `refresh_forced_choice_diagnostic_ready`
- Input: one or more coexistence refresh reports
- Candidate terms: `fixed/loss`
- Scoring: teacher-forced candidate NLL and first-token rank

## Validation

```text
python -m pytest tests\test_model_capability_required_term_pair_refresh_forced_choice_diagnostic.py -q -o cache_dir=runs\pytest-cache-v616-targeted
5 passed
```

## Next Action

Run the diagnostic over v611-v613 real checkpoints.
