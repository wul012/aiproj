# aiproj A3 Artifact Schema Guard

v1265 completes the second A3 slice by adding a fail-closed schema guard for
current card and publication-receipt artifacts.

## Scope

The guard validates artifact shape only. It does not rebuild cards, retrain
models, change cached verdicts, or promote a checkpoint.

## Registry

The source of truth is:

```text
docs/artifact-schema-guard-registry.json
```

The initial schemas cover:

- `experiment_card_v1`
- `dataset_card_v1`
- `model_card_v1`
- `publication_receipt_v1`

The first three use current v1265 card samples generated from existing archived
fixture inputs. The publication receipt schema uses the real v999 receipt
artifact and keeps no-promotion fields explicit.

## Gate

Run:

```powershell
python -B scripts/check_artifact_schema_guard.py --out-dir runs/artifact-schema-guard
```

The checker fails when a registered artifact is missing, is not a JSON object,
loses a required field, violates an expected value, or changes the type of a
registered field.

The v1265 evidence bundle lives under `f/1265/解释/artifact-schema-guard/`;
schema sample artifacts used by the registry live under
`f/1265/解释/schema-samples/`.

## CI Role

CI runs this gate after `check_model_capability_honest_measurement.py` and
before coverage. The honest-measurement gate protects the claim boundary; this
schema gate protects the artifact envelope.
