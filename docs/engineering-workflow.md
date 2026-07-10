# MiniGPT Engineering Workflow

This page records the standard local workflow for maintainers. It focuses on
the current normalized path rather than the long historical version ledger.

## Environment

Install the declared dependencies from the repository root:

```powershell
python -m pip install --upgrade pip
pip install -r requirements.txt
```

The project uses a `src/` layout declared in `pyproject.toml`. Runtime package
discovery comes from `src/minigpt`, and local pytest discovery is scoped to
`tests/`.

## CI Execution Economy

The primary workflow runs for pull requests and pushes to `main`. Release tags
pointing at an already-tested main commit do not trigger a duplicate full run.
`actions/setup-python` caches pip downloads using `requirements.txt` as the
invalidation source, and same-ref concurrency cancels a superseded run when a
newer commit arrives. These settings reduce duplicate compute without skipping
or caching test results. `scripts/check_ci_workflow_hygiene.py` fails if the
trigger scope, cache, or cancellation contract drifts. See
`docs/ci-execution-economy.md` for the exact policy.

## Standard Checks

For the current maintainer health check:

```powershell
python -B scripts/check_engineering_health.py
```

This runs the `HEALTH_ENGINEERING_ENTRYPOINTS` subset from
`scripts/_bootstrap.py`: source encoding hygiene, project documentation
readability, CI workflow hygiene, staged static analysis, scoped type analysis,
model-capability honest measurement, artifact schema guard, file-size ratchet,
the A-track closeout gate, and the normalization guard in one local command. Source encoding, docs
readability, CI workflow, static-analysis, type-analysis, honest-measurement,
artifact-schema, file-size, and A-track closeout reports are written under
`runs/engineering-health/`, and the aggregate command writes
`runs/engineering-health/engineering_health_summary.json` and
`runs/engineering-health/engineering_health_summary.md` with the step commands,
return codes, and pass/fail status.

For the staged ruff gate alone:

```powershell
python -B scripts/check_static_analysis.py --out-dir runs/static-analysis
```

This compares current `src/` and `scripts/` ruff findings against
`docs/static-analysis/ruff-baseline.json`, fails on new findings, and requires
the strict maintained path set to pass `ruff format --check`. See
`docs/static-analysis.md` for the baseline and update policy.

For the scoped strict mypy gate alone:

```powershell
python -B scripts/check_type_analysis.py --out-dir runs/type-analysis
```

This reads `docs/static-analysis/mypy-scope.json`, validates its scope floor and
group assignments, then checks only the declared load-bearing files. Scope and
type failures both return a non-zero exit code.

For the model-capability honest-measurement gate alone:

```powershell
python -B scripts/check_model_capability_honest_measurement.py --out-dir runs/model-capability-honest-measurement
```

This reads `docs/model-capability-honest-measurement-registry.json` and checks
that registered capability-governance families are cached-artifact-only,
no-promotion, seed-policy bounded, backed by existing source artifacts, and
protected by positive plus negative contract-test markers.

For the artifact schema guard alone:

```powershell
python -B scripts/check_artifact_schema_guard.py --out-dir runs/artifact-schema-guard
```

This reads `docs/artifact-schema-guard-registry.json` and checks current
experiment-card, dataset-card, model-card, and publication-receipt artifact
envelopes for required fields, expected values, and simple field types.

For the file-size ratchet alone:

```powershell
python -B scripts/check_file_size_ratchet.py --out-dir runs/file-size-ratchet
```

This reads `docs/code-health/file-size-ratchet.json` and scans Python files
under `src/`, `scripts/`, and `tests/`. Unwaived files above the hard line
limit fail, and waived legacy oversize tests must not grow beyond their
committed baseline.

For the A-track final evidence closeout alone:

```powershell
python -B scripts/check_aiproj_track_closeout.py --out-dir runs/aiproj-track-closeout
```

This checks `docs/aiproj-track-final-evidence.md`, A0-A4 evidence docs,
no-promotion wording, documentation indexes, and CI closeout gate wiring. It is
the maintainer command to run before treating the production-excellence A-track
as review-ready.

For a quick full unittest run:

```powershell
python -m unittest discover -s tests -v
```

For the same coverage-producing entrypoint used by CI:

```powershell
python -B scripts/run_test_coverage.py --out-dir runs/test-coverage --fail-under 88.98
```

The `88.98` floor is the A2 ratchet recorded in
`docs/static-analysis/coverage-floor.json`: v1262 measured `90.98%`, and A2
starts CI enforcement at baseline minus two points.

For architecture and public API normalization work, run the focused guard set:

```powershell
python -B scripts/check_normalization_guard.py
```

For the warning-only archive and `runs/` inventory:

```powershell
python -B scripts/check_archive_runs_inventory.py --out-dir runs/archive-runs-inventory --force
```

For the documentation navigation/readability split alone:

```powershell
python -B scripts/check_project_docs_readability.py --require-pass --force
```

The stable documentation checker writes `project_docs_readability.*` outputs.
Versioned devtool wrappers may keep versioned output names for archive
compatibility, but maintainer workflows should use the stable script above.
For the short map of stable maintainer scripts versus historical wrappers, see
`docs/script-entrypoints.md`.

CI runs the same project docs readability check and normalization guard before
the coverage-producing unittest entrypoint, so documentation-navigation and
import-boundary regressions fail with focused signals first. The CI workflow
hygiene report treats both commands as required steps and checks that they
remain before coverage.

## What These Guards Protect

- `tests/test_architecture_boundaries.py` protects the first normalized import
  boundaries for core and owner packages.
- `tests/test_script_import_boundaries.py` protects active CLI scripts so new
  core, training, evaluation, serving, report, and governance commands import
  from owner packages instead of drifting back to flat implementation modules.
- `tests/test_public_api_policy.py` protects Tier 1 imports and legacy facade
  compatibility.
- `tests/test_foundation_package_reexports.py` protects `core`, `training`,
  `evaluation`, and `serving` migration surfaces.
- `tests/test_evidence_package_reexports.py` protects `reports` and
  `governance` migration surfaces.
- `tests/test_source_encoding_hygiene.py` protects the source-encoding report
  contract, CLI exit behavior, and Python parser target compatibility checks.
- `tests/test_ci_workflow.py` protects CI workflow hygiene policy from
  `ci_workflow_hygiene_policy.py`, required CI commands, and pre-coverage
  ordering for documentation, evidence, and normalization gates.
- `tests/test_static_analysis.py` protects the staged ruff baseline comparison,
  strict-path lint behavior, strict format behavior, CLI baseline update path,
  and JSON/CSV/Markdown/HTML report writers.
- `tests/test_type_analysis.py` protects the committed mypy scope floor, group
  assignments, diagnostic parsing, strict failure behavior, and report bundle.
- `tests/test_test_coverage_report.py` protects the coverage report model,
  threshold behavior, output renderers, and the coverage CLI entrypoint
  contract.
- `tests/test_project_configuration.py` also locks the committed coverage
  floor against the CI workflow and workflow-hygiene policy.
- `tests/test_project_configuration.py` protects `pyproject.toml`,
  `requirements.txt`, CI, and the documented unittest entrypoint.
- `tests/test_repository_hygiene.py` protects `.gitignore` coverage for local
  caches, virtual environments, generated reports, editor files, and the
  personal `ignoreit.py` scratch file.
- `tests/test_project_docs_readability.py` protects the README and `docs/`
  navigation split, plus the `START_HERE.md` and `docs/README.md` front-door
  files, so normalization guidance remains discoverable and readable.

The `scripts/check_normalization_guard.py` wrapper is intentionally thin. It
prints and runs the focused `unittest` modules above, then returns the same exit
code as the underlying test command. The focused module list lives in
`scripts/_normalization_guard.py` so the CLI and bootstrap tests share one
configuration source. For the maintained module-by-module inventory, see
`docs/normalization-guard.md`.

Current engineering entrypoints listed by
`BOOTSTRAPPED_ENGINEERING_ENTRYPOINTS` in `scripts/_bootstrap.py` share one
project-root and `src/` path setup. This keeps CI and local checks from growing
separate copies of the same startup snippet while leaving historical one-off
scripts untouched.

The aggregate health steps are built in `scripts/_engineering_health.py` from
the `HEALTH_ENGINEERING_ENTRYPOINTS` list, keeping the local health command as
a thin runner over stable checks instead of a second implementation of those
checks. It also runs the docs readability and static-analysis checks as
first-class steps, so navigation and ruff regressions produce their own report
directories instead of being visible only through broader guards. Its top-level
summary is intentionally small and available as JSON plus Markdown; detailed
evidence stays in each child check's report directory.

The active normalization tests share `tests/_bootstrap.py` for the same reason:
current guard tests, including the CI workflow hygiene tests, get a single
tested project-root and `src/` setup point, while older historical tests can
migrate only when they become active maintenance surfaces.

The repository still contains many historical governance and research modules.
These checks are the current safety rail for the parts being normalized, not a
claim that every historical chain has already been physically moved.

## Generated And Local Files

Generated run evidence belongs under `runs/` unless a versioned archive
explicitly needs to preserve it elsewhere. Local caches such as `__pycache__/`,
`.pytest_cache/`, `.coverage`, `htmlcov/`, virtual environments, and browser
test output should remain untracked. Editor settings under `.vscode/` or
`.idea/` are local workspace state. The root `ignoreit.py` file is intentionally
ignored as a personal practice scratch file.

The archive roots `a/`, `b/`, `c/`, `d/`, `e/`, and `f/` are path-stable
historical evidence. Use `scripts/check_archive_runs_inventory.py` to measure
their growth, but do not relocate old evidence as part of routine cleanup.
