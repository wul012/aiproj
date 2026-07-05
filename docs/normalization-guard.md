# MiniGPT Normalization Guard

This page explains the focused normalization guard used while the project is
being moved back toward a maintainable software-engineering shape. It is a
maintainer map for the current guard set, not a claim that every historical
experiment path is already normalized.

Run the guard from the repository root:

```powershell
python -B scripts/check_normalization_guard.py
```

The command is intentionally thin. It builds one unittest command from
`FOCUSED_TEST_MODULES` in `scripts/_normalization_guard.py`, prints that command,
runs it, and returns the same exit code. The module list is the single source
of truth for this focused guard.

## Guarded Modules

- `tests.test_architecture_boundaries` protects owner-package import direction
  so normalized inner layers do not depend on report, governance, or serving
  layers. It also enforces the `transitional package files stay small` guard so
  the new owner packages remain compatibility facades instead of becoming large
  implementation dumps, and checks that owner-package `__all__` export tables
  stay unique and resolvable. It also keeps owner package initializers as
  facade-only package initializers: module docstring, owner submodule imports,
  and `__all__`, not embedded implementation code. The same guard keeps
  owner-package imports aligned with `__all__` so package namespaces do not
  accumulate hidden re-export drift. During this transitional phase, owner
  package submodules also stay as facade-only transitional submodules until a
  future physical module move deliberately updates the guard, and those
  submodules must keep their explicit imports aligned with `__all__`. Their
  submodule `__all__` tables must also stay list-based, unique, and resolvable.
- `tests.test_script_import_boundaries` protects active CLI scripts from
  drifting back to flat implementation-module imports when owner packages now
  exist.
- `tests.test_public_api_policy` protects Tier 1 imports and compatibility
  expectations for public API surfaces.
- `tests.test_foundation_package_reexports` protects the `core`, `training`,
  `evaluation`, and `serving` compatibility packages.
- `tests.test_evidence_package_reexports` protects `reports` and `governance`
  compatibility packages, including the owner-level `minigpt.reports.utils`
  report helper surface.
- `tests.test_engineering_health` protects the aggregate engineering-health
  step model, summary model, and local health CLI behavior.
- `tests.test_report_utils` protects shared report-output bundle helpers used
  by the active engineering checks, and keeps the lower-level readability
  artifact path on `minigpt.report_utils` to avoid reintroducing a reports
  package import cycle.
- `tests.test_report_utils_helpers` protects the generic report utility
  helpers for artifact rows, archived reference paths, JSON/CSV writers,
  Markdown/HTML/CSV cell escaping, list and number normalization, and CI
  regression-reason counts.
- `tests.test_source_encoding_hygiene` protects the source-encoding report
  model, CLI exit behavior, and Python parser-target compatibility checks.
- `tests.test_ci_workflow` protects CI workflow hygiene policy, required CI
  commands, report renderers, and pre-coverage ordering.
- `tests.test_test_coverage_report` protects the coverage report model,
  threshold behavior, output renderers, and the coverage CLI entrypoint
  contract.
- `tests.test_project_configuration` protects `pyproject.toml`,
  `requirements.txt`, CI command wiring, and documentation index expectations.
- `tests.test_repository_hygiene` protects ignore rules for caches, generated
  local outputs, editor state, virtual environments, and the personal
  `ignoreit.py` scratch file.
- `tests.test_script_bootstrap` protects shared script/test bootstrap behavior,
  tests-package import bootstrapping for direct unittest module runs, CI
  engineering entrypoint partitioning, the already-normalized registry/release/
  benchmark/training-portfolio/training-scale/server test bootstrap families,
  and the normalization wrapper CLI.
- `tests.test_script_bootstrap_helpers` protects the small AST and path helper
  functions used by the script bootstrap tests, including function lookup,
  argument-name extraction, `SystemExit(main(...))` detection,
  `if __name__ == "__main__"` detection, and repository-relative script module
  name conversion.
- `tests.test_script_surface_registry` protects the canonical script surface
  registry, current maintained script partition, import-safe maintained script
  surface, support module export tables, support module non-runnable boundary,
  and stable script entrypoint documentation.
- `tests.test_script_cli_contracts` protects current stable script CLI
  contracts, shared `_bootstrap` usage, `main(argv)->int`,
  `parse_args(["--help"])` behavior, and active CLI mojibake text hygiene.
- `tests.test_active_cli_coverage` protects active CLI group partitioning,
  import-boundary coverage alignment, and the `ACTIVE_CLI_BEHAVIOR_COVERAGE`
  assignment table that points every active CLI to a focused behavior test
  module.
- `tests.test_active_cli_behavior` protects lightweight foundation data and
  analysis CLI behavior by calling selected `main([...])` entrypoints with
  temporary inputs and real output assertions for dataset preparation,
  tokenizer inspection, history plotting, run comparison, and generation
  quality.
- `tests.test_model_cli_behavior` protects tiny-checkpoint foundation model CLI
  behavior for evaluation, fixed prompt suites, generation, next-token
  prediction, attention inspection, one-shot chat, and tiny CPU training.
- `tests.test_serving_cli_behavior` protects the playground server CLI with a
  fake server so the endpoint contract is tested without leaving a background
  process running.
- `tests.test_report_cli_behavior` protects report-oriented active CLI
  behavior by building temporary dashboard, dataset-card, experiment-card, and
  model-card evidence, plus a tiny model-inspection report, through their
  `main([...])` entrypoints.
- `tests.test_governance_cli_behavior` protects governance-oriented active CLI
  behavior by building temporary registry, release-bundle, release-gate, and
  release-readiness evidence through their `main([...])` entrypoints.
- `tests.test_governance_extended_cli_behavior` protects the remaining
  governance-oriented active CLI behavior for maturity summaries, maturity
  narratives, release-readiness comparisons, drift-contract checks, and release
  gate profile comparisons.
- `tests.test_project_docs_readability` protects the root README, `docs/`
  split, front-door navigation files, and known mojibake guards.

## Active CLI Behavior Coverage

`tests.test_active_cli_coverage` owns the `ACTIVE_CLI_BEHAVIOR_COVERAGE`
assignment table. That table must cover every path in
`BOOTSTRAPPED_ACTIVE_CLI_ENTRYPOINTS` exactly once and must point each active
script to a focused behavior test module. When a new active CLI is added to
`scripts/_bootstrap.py`, it must either be assigned to an existing behavior
test module or get a new focused behavior test before the normalization guard
can pass.

## What This Guard Does Not Prove

The guard is deliberately focused. It proves the currently normalized
maintenance surface: owner-package imports, stable maintainer scripts, CI and
coverage gates, source hygiene, repository hygiene, and documentation
navigation.

It does not prove that every historical training, governance, or research
script has been refactored. Historical and versioned paths should only be added
to this guard when they become active maintenance surfaces again and have a
clear owner boundary.

## Update Rule

When adding a module to `FOCUSED_TEST_MODULES`, update this page in the same
change. The guard list, workflow documentation, and project docs readability
check should move together so maintainers can see what the focused guard means
without reading Python source first.
