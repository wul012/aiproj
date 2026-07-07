# aiproj A4 Code Health

v1266 completes the production-excellence A4 slice by adding a mechanical
file-size ratchet for current Python code.

## Scope

The gate measures Python file size under `src/`, `scripts/`, and `tests/`.
It does not split legacy tests in this version, does not move historical
archives, does not change model training behavior, and does not alter cached
experiment verdicts.

## Registry

The source of truth is:

```text
docs/code-health/file-size-ratchet.json
```

The policy uses two thresholds:

- `warning_line_limit=500`: files above this line are visible in the report.
- `max_line_limit=800`: unwaived files above this line fail the gate.

Eight existing legacy test files exceed the hard limit. They are recorded as
explicit waivers with baseline line counts, reasons, and follow-up split
directions. A waiver is not permission to keep growing: if the current line
count rises above the committed baseline, the gate fails.

## Gate

Run:

```powershell
python -B scripts/check_file_size_ratchet.py --out-dir runs/file-size-ratchet
```

The checker writes JSON, CSV, Markdown, and HTML. The summary includes scanned
file count, warning count, over-limit count, waiver count, unwaived over-limit
count, waiver growth violations, and the largest file path.

## CI Role

CI runs this gate after `check_artifact_schema_guard.py` and before coverage.
That placement keeps A3 artifact contracts ahead of A4 maintainability checks,
then lets coverage run after the cheaper fail-fast gates.

## Current Boundary

The current production and script code is below the hard limit. The over-limit
surface is legacy tests, so this version chooses a no-growth ratchet instead of
a risky broad split. Future work can split those waived tests one family at a
time, then lower or remove each waiver as the line count shrinks.
