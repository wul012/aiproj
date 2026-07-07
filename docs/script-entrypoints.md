# MiniGPT Script Entrypoints

This page lists the stable maintainer script entrypoints for the current
normalization path. It is a navigation map, not a complete inventory of every
historical experiment script in `scripts/`.

## Stable Maintainer Checks

Use these commands from the repository root when maintaining the current
software-engineering surface:

### Local Aggregate

```powershell
python -B scripts/check_engineering_health.py
```

`scripts/check_engineering_health.py` is the broad local maintainer check. It
runs the `HEALTH_ENGINEERING_ENTRYPOINTS` subset: source-encoding hygiene,
project documentation readability, CI workflow hygiene, staged static analysis,
scoped type analysis, model-capability honest measurement, and the normalization
guard, then writes a compact top-level summary. It is
intentionally local-only because CI already runs the underlying gates as
separate fail-fast steps.

### CI-Backed Gates

```powershell
python -B scripts/check_source_encoding.py
python -B scripts/check_project_docs_readability.py --require-pass --force
python -B scripts/check_ci_workflow_hygiene.py
python -B scripts/check_static_analysis.py --out-dir runs/static-analysis
python -B scripts/check_type_analysis.py --out-dir runs/type-analysis
python -B scripts/check_model_capability_honest_measurement.py --out-dir runs/model-capability-honest-measurement
python -B scripts/check_artifact_schema_guard.py --out-dir runs/artifact-schema-guard
python -B scripts/check_normalization_guard.py
python -B scripts/run_test_coverage.py --out-dir runs/test-coverage --fail-under 88.98
```

Stable maintainer scripts expose a testable `main(...)->int` entrypoint and use
`raise SystemExit(main(...))` when run as scripts. This keeps local commands,
CI commands, and direct unit tests on the same exit-code contract.

Current maintained scripts must also be import-safe: importing or reloading the
script module should not print output, run the command body, start servers,
read checkpoints, or write evidence. The command body belongs behind
`main(...)`; the module top level is reserved for imports, constants, and
function definitions. Active CLI help is tested through `parse_args(["--help"])`
so parser regressions are caught without spawning every command in a subprocess.

The CI-backed gate list is mirrored by `scripts/_bootstrap.py`,
`src/minigpt/ci_workflow_hygiene.py`, and `.github/workflows/ci.yml`. The
health subset lives in `HEALTH_ENGINEERING_ENTRYPOINTS`, while coverage remains
a CI-backed gate outside the quick aggregate health command. The normalization
guard tests that these surfaces stay aligned.

`scripts/check_normalization_guard.py` is the focused architecture and project
contract check. Use it when changing owner packages, active script imports,
public API surfaces, repository hygiene, project configuration, or the
normalized documentation map.

`scripts/check_project_docs_readability.py` protects the reader-facing docs
split. It checks that key docs exist, are linked from the root README, contain
their expected headings and terms, and that the front-door files avoid known
mojibake markers.

`scripts/check_source_encoding.py` catches text-encoding regressions before
they spread into README, docs, or generated report surfaces.

`scripts/check_ci_workflow_hygiene.py` checks that CI still installs the
declared requirements, runs the project docs readability check and
static-analysis and normalization guards before coverage, and keeps the
required workflow steps visible.

`scripts/check_static_analysis.py` runs the staged ruff gate. It compares
current `src/` and `scripts/` findings against
`docs/static-analysis/ruff-baseline.json`, fails on new findings, and keeps the
strict maintained path set lint-clean and format-clean.

`scripts/check_type_analysis.py` runs strict mypy over the committed scope in
`docs/static-analysis/mypy-scope.json`. The scope floor and group assignments
prevent the checked surface from shrinking silently, while the report bundle
keeps diagnostics and the exact target list reviewable.

`scripts/check_model_capability_honest_measurement.py` validates the A3
honest-measurement registry. It keeps bounded model-capability governance
claims tied to cached artifacts, no-promotion boundaries, seed-policy labels,
and positive/negative contract-test markers.

`scripts/check_artifact_schema_guard.py` validates the A3 artifact schema
registry. It keeps current card and publication-receipt envelopes fail-closed
against required fields, selected expected values, and simple field types.

`scripts/run_test_coverage.py` is the coverage-producing unittest entrypoint
used by CI. The local command above writes coverage evidence under
`runs/test-coverage/`. The current `88.98` floor is recorded in
`docs/static-analysis/coverage-floor.json`; raise it only with fresh evidence,
and do not lower it as a routine cleanup.

## Shared Support Modules

These modules are support code for the stable maintainer entrypoints:

- `scripts/_bootstrap.py` defines the project root, `src/` root, and the active
  bootstrapped engineering entrypoint list.
- `scripts/_normalization_guard.py` owns the focused unittest module list and
  command builder used by the normalization wrapper.
- `scripts/_engineering_health.py` owns the engineering-health step model,
  command construction, summary model, and JSON/Markdown summary writers.

Keeping these pieces behind underscored helper modules prevents every current
script from carrying its own copy of path setup, focused test selection, and
summary rendering.

`SCRIPT_SUPPORT_MODULES` in `scripts/_bootstrap.py` is the canonical support
module list. Support modules are internal helper modules.
They are not runnable maintainer entrypoints, so they stay outside
`CURRENT_MAINTAINED_SCRIPT_ENTRYPOINTS`.

Each support module keeps an explicit support module `__all__` table. The
bootstrap tests check that those tables are lists, contain no duplicate names,
and resolve to real module attributes, so the helper surface remains deliberate
instead of becoming another implicit public namespace.

Support modules are also import-safe: importing or reloading them should not
print output, run checks, or write evidence. They provide helper functions,
constants, and small data models; command execution still belongs in the
stable entrypoint scripts that call them.

## Current Maintained Script Surface

`CURRENT_MAINTAINED_SCRIPT_ENTRYPOINTS` in `scripts/_bootstrap.py` is the
canonical current maintenance surface for scripts. It is intentionally just the
union of `BOOTSTRAPPED_ENGINEERING_ENTRYPOINTS` and
`BOOTSTRAPPED_ACTIVE_CLI_ENTRYPOINTS`.

The script surface constants in `scripts/_bootstrap.py` are tuple-based
collections of repository-relative POSIX `.py` paths. They should not contain
absolute paths, Windows separators, generated-output locations, or mutable
lists; the bootstrap tests treat that path shape as part of the maintainer
contract.

`SCRIPT_ENTRYPOINT_SURFACES` is the canonical registry of those entrypoint
surface constants. Tests use that registry instead of maintaining a duplicate
surface map, so adding or removing a maintained script surface happens in one
place.

The active CLI half is split by owner area in `FOUNDATION_ACTIVE_CLI_ENTRYPOINTS`,
`REPORT_ACTIVE_CLI_ENTRYPOINTS`, and `GOVERNANCE_ACTIVE_CLI_ENTRYPOINTS`, then
combined into the bootstrapped active CLI tuple. The split is only a navigation
aid; `BOOTSTRAPPED_ACTIVE_CLI_ENTRYPOINTS` remains the tested active CLI set.

This means a script can exist in `scripts/` without being part of the current
maintenance surface. Versioned scripts, route-specific experiments, archive
smokes, and compatibility helpers stay outside this tuple until a current
consumer proves that they should be promoted.

## Normalized Active CLIs

These active user-facing CLIs are not CI gates, but they now share the same
project-root and `src/` path bootstrap instead of carrying separate
`sys.path.insert` snippets:

### Foundation, Evaluation, Training, And Serving

This group exposes the same testable command contract used by maintainer
checks: each script has `parse_args(argv)` and `main(argv)->int`, then uses
`raise SystemExit(main())` when run directly.

- `scripts/analyze_generation_quality.py`
- `scripts/chat.py`
- `scripts/compare_runs.py`
- `scripts/eval_suite.py`
- `scripts/evaluate.py`
- `scripts/generate.py`
- `scripts/inspect_attention.py`
- `scripts/inspect_predictions.py`
- `scripts/inspect_tokenizer.py`
- `scripts/plot_history.py`
- `scripts/prepare_dataset.py`
- `scripts/serve_playground.py`
- `scripts/train.py`

### Reports

This group also exposes `parse_args(argv)` and `main(argv)->int`, then uses
`raise SystemExit(main())` when run directly.

- `scripts/build_dashboard.py`
- `scripts/build_dataset_card.py`
- `scripts/build_experiment_card.py`
- `scripts/build_model_card.py`
- `scripts/inspect_model.py`

### Governance

This group also exposes `parse_args(argv)` and `main(argv)->int`. Gate-style
commands return their policy decision code from `main(...)`; the direct script
entrypoint turns that return value into the process exit code.

- `scripts/build_maturity_narrative.py`
- `scripts/build_maturity_summary.py`
- `scripts/build_release_bundle.py`
- `scripts/build_release_readiness.py`
- `scripts/check_release_gate.py`
- `scripts/check_release_readiness_drift_contract.py`
- `scripts/compare_release_gate_profiles.py`
- `scripts/compare_release_readiness.py`
- `scripts/register_runs.py`

They are the current normalized active CLI batch because they already import
from owner packages such as `minigpt.core.*`, `minigpt.evaluation.*`,
`minigpt.governance.*`, `minigpt.reports.*`, `minigpt.serving.*`, and
`minigpt.training.*`. Future active CLI migrations should add to this list only
after their reusable imports have an owner-package path and a focused boundary
test. Active CLIs should also avoid the root `minigpt` facade; that facade is a
compatibility surface, not the preferred import path for maintained commands.

### Behavior Coverage Rule

Every script in `BOOTSTRAPPED_ACTIVE_CLI_ENTRYPOINTS` must also be assigned in
`ACTIVE_CLI_BEHAVIOR_COVERAGE` inside `tests/test_active_cli_coverage.py`. That
assignment points the script to the focused behavior test module that calls its
`main([...])` entrypoint with temporary inputs and checks real stdout or output
files. Adding an active CLI without this assignment leaves the command surface
under-specified, so the normalization guard fails until the behavior test
coverage is explicit.

### Text Hygiene

Active CLI files are also guarded against common mojibake fragments in
user-facing defaults such as prompt, system, and text examples. Historical
scripts can keep archived text as evidence, but current CLI defaults should be
readable UTF-8 so a maintainer can run `--help` or a default command without
copying corrupted example text forward.

## Outputs

The default local evidence locations are:

- `runs/engineering-health/engineering_health_summary.json`
- `runs/engineering-health/engineering_health_summary.md`
- `runs/engineering-health/source-encoding/`
- `runs/engineering-health/project-docs-readability/`
- `runs/engineering-health/ci-workflow-hygiene/`
- `runs/engineering-health/static-analysis/`
- `runs/engineering-health/type-analysis/`
- `runs/test-coverage/`

Use `tmp/` only for throwaway local validation while working. Final maintainer
evidence should use the stable `runs/` locations or a versioned archive when a
version explicitly needs preserved evidence.

## Historical And Versioned Scripts

The repository intentionally still contains many historical, versioned, or
route-specific scripts. Examples include older analysis runners, experiment
drivers, report builders, and compatibility wrappers under `scripts/` and
`scripts/devtools/`.

Those files are historical surfaces unless an active consumer proves they are
part of the current maintenance path. Do not migrate or rename them just to
make the tree look tidy. When one becomes active again, first give it a stable
owner import path, add a focused test, and only then decide whether it belongs
in the stable maintainer entrypoint list.

### Promotion Rule

Promote a historical script into the current maintenance surface only after it
has a real current CLI, CI, or documented maintainer consumer; imports reusable
code through owner packages instead of flat compatibility modules; uses
`scripts/_bootstrap.py` for project-root and `src/` setup; has a focused
boundary test; and is listed in both `BOOTSTRAPPED_ACTIVE_CLI_ENTRYPOINTS` or
the engineering entrypoint tuple and this document.

`scripts/devtools/check_project_docs_readability_v1131.py` is a compatibility
wrapper. It keeps the legacy `project_docs_readability_v1131.*` output names
for archive continuity, while new maintainer docs should point to
`scripts/check_project_docs_readability.py`.
