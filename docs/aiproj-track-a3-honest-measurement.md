# aiproj A3 Honest Measurement Gate

v1264 starts production-excellence A3 by turning model-capability honesty rules
into a committed mechanical gate.

## Scope

This is an engineering/governance-lane check. It validates registry entries,
source artifacts, selected artifact fields, and the existence of positive plus
negative contract-test markers. It does not retrain models, change cached
experiment outputs, alter `decide()` semantics, or promote any checkpoint.

## Registry

The source of truth is:

```text
docs/model-capability-honest-measurement-registry.json
```

The initial registry deliberately covers only representative families that
already have contract checks:

- `baseline-candidate-handoff-v433-v434`
- `route-promotion-release-readiness-v1258-v1259`

Future capability families should be added here before their bounded claim is
used as production-excellence evidence.

## Gate

Run the checker with:

```powershell
python -B scripts/check_model_capability_honest_measurement.py --out-dir runs/model-capability-honest-measurement
```

The checker fails if a family is not cached-artifact-only, if it allows
promotion authority, if single-seed stochastic evidence is not labeled
exploratory/no-promotion, if registered artifacts are missing, if guarded fields
drift, or if the positive/negative contract-test markers disappear.

## CI Role

CI runs this gate after scoped type analysis and before coverage. The ordering
matters: capability-claim boundaries should fail with a focused signal before
the expensive coverage-producing test run.
