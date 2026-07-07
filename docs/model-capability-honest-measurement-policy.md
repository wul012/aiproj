# Model Capability Honest Measurement Policy

This policy supports the A3 production-excellence gate. It applies to the
engineering/governance lane only: reports, receipts, indexes, reviews, and contract
checks may be validated here, but cached experiment verdicts and model-training
semantics stay untouched.

## Rules

- Capability claims must be bounded by the evidence type that produced them.
- Cached-artifact checks must re-read committed artifacts; they must not retrain a model.
- A stochastic pass/fail claim requires multi-seed evidence before it can be described as
  seed-stable.
- Single-seed or smoke-style evidence must remain `exploratory`, `not_claimed`, or
  explicitly no-promotion.
- Publication, handoff, and route-promotion receipts must keep promotion authority out
  of the artifact unless a separate review gate grants it.
- Every registered capability family must have at least one positive contract marker and
  one negative/tamper/missing-source marker in committed tests.

## Mechanical Gate

The committed registry is
`docs/model-capability-honest-measurement-registry.json`. The CI gate is:

```powershell
python -B scripts/check_model_capability_honest_measurement.py --out-dir runs/model-capability-honest-measurement
```

The checker validates registry schema, source artifact existence, selected artifact
fields, no-training flags, promotion boundary fields, seed-policy labels, and test
markers. A failure means the project may still have useful science artifacts, but the
engineering lane cannot honestly claim the registered capability family is protected by
the A3 governance contract.
