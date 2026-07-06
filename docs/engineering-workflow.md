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

## Standard Checks

For the current maintainer health check:

```powershell
python -B scripts/check_engineering_health.py
```

This runs the `HEALTH_ENGINEERING_ENTRYPOINTS` subset from
`scripts/_bootstrap.py`: source encoding hygiene, project documentation
readability, CI workflow hygiene, staged static analysis, and the normalization
guard in one local command. Source encoding, docs readability, CI workflow, and
static-analysis reports are written under `runs/engineering-health/`, and the aggregate command writes
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

For a quick full unittest run:

```powershell
python -m unittest discover -s tests -v
```

For the same coverage-producing entrypoint used by CI:

```powershell
python -B scripts/run_test_coverage.py --out-dir runs/test-coverage --fail-under 80
```

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
- `tests/test_test_coverage_report.py` protects the coverage report model,
  threshold behavior, output renderers, and the coverage CLI entrypoint
  contract.
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
