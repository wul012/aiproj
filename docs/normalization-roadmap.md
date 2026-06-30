# MiniGPT Normalization Roadmap

This roadmap records how the project is being moved back toward a maintainable
software-engineering shape. It is intentionally about the active normalization
path, not the full historical version ledger.

## Current Phase

The current phase is a contract-preserving package split. The project still
keeps historical flat modules such as `model.py`, `eval_suite.py`,
`release_gate.py`, and `model_report.py`, but new owner packages now provide
clearer import paths:

- `minigpt.core` for model, tokenizer, dataset, history, and RoPE primitives.
- `minigpt.training` for data preparation, quality checks, history, runtime,
  corpus setup, and LM training helpers.
- `minigpt.evaluation` for prompt suites, run comparisons, generation quality,
  and suite-design summaries.
- `minigpt.serving` for local generation, contracts, routes, checkpoint
  discovery, HTTP helpers, request history, and server assembly.
- `minigpt.reports` for model reports, cards, dashboards, manifests, and
  artifact maps.
- `minigpt.governance` for active release, maturity, and registry governance
  facades.

The package split is transitional. It gives new code stable owner-level import
paths before old flat modules are physically moved or retired.

## What Is Already Guarded

The current guard set is deliberately narrow and evidence-backed:

- `tests/test_public_api_policy.py` keeps Tier 1 imports, legacy facade
  compatibility, and the root facade export budget visible.
- `tests/test_foundation_package_reexports.py` verifies that core, training,
  evaluation, and serving packages re-export the same objects as the old flat
  modules.
- `tests/test_evidence_package_reexports.py` does the same for reports and
  governance.
- `tests/test_source_encoding_hygiene.py` protects the source-encoding report
  contract, CLI exit behavior, and Python parser target compatibility checks.
- `tests/test_ci_workflow.py` protects CI workflow hygiene policy, required
  CI commands, and pre-coverage ordering for documentation, evidence, and
  normalization gates.
- `tests/test_test_coverage_report.py` protects the coverage report model,
  threshold behavior, output renderers, and the coverage CLI entrypoint
  contract.
- `tests/test_report_utils.py` protects the shared report-output bundle helper
  and keeps active engineering report writers on the owner-level
  `minigpt.reports.utils` import path where dependency direction allows it.
- `tests/test_report_utils_helpers.py` keeps generic `minigpt.report_utils`
  helper semantics covered separately from the report-output bundle and import
  boundary tests.
- `tests/test_architecture_boundaries.py` prevents the normalized inner layers
  from importing outer governance/report layers and keeps the transitional
  owner-package files small enough to stay facade-oriented.
- `tests/test_script_import_boundaries.py` keeps active CLI scripts on owner
  package imports instead of drifting back to flat implementation modules.
- `tests/test_project_configuration.py` protects `pyproject.toml`,
  `requirements.txt`, CI, and the standard unittest entrypoint.
- `tests/test_repository_hygiene.py` protects ignore rules for caches, local
  editor state, generated outputs, virtual environments, and the personal
  `ignoreit.py` scratch file.
- `tests/test_project_docs_readability.py` protects the normalized README and
  `docs/` navigation split.

Run the current focused set through the stable wrapper:

```powershell
python -B scripts/check_normalization_guard.py
```

The focused guard module list is centralized in
`scripts/_normalization_guard.py`, which keeps the CLI command and the tests
that inspect guard membership from drifting apart. The reader-facing inventory
for that list lives in `docs/normalization-guard.md`.

For a broader local maintainer pass, `scripts/check_engineering_health.py`
aggregates source encoding hygiene, project documentation readability, CI
workflow hygiene, and the normalization guard. Its step list lives in
`scripts/_engineering_health.py` so the wrapper does not duplicate check logic.
The command writes a top-level
`engineering_health_summary.json` plus `engineering_health_summary.md` that
record step commands, return codes, and pass/fail status while leaving detailed
evidence in child report directories.

The current CI and normalization entrypoints listed by
`BOOTSTRAPPED_ENGINEERING_ENTRYPOINTS` in `scripts/_bootstrap.py` also share one
project-root and `src/` path setup. This is intentionally scoped to active
engineering entrypoints first; historical one-off research scripts can migrate
only when they become active maintenance surfaces.

The same rule now applies to the active normalization test set through
`tests/_bootstrap.py`, keeping current guard tests off repeated local
`sys.path` snippets without rewriting the full historical test suite.

CI workflow hygiene now treats `scripts/check_project_docs_readability.py` and
`scripts/check_normalization_guard.py` as required pre-coverage gates, so the
documentation and normalization checks cannot quietly disappear from the
workflow.

The stable documentation readability entrypoint is
`scripts/check_project_docs_readability.py`. Older versioned devtool wrappers
can remain for archive compatibility, but new workflow docs should point at the
stable script name. The check now also treats `START_HERE.md` and
`docs/README.md` as front-door files with required navigation terms and
mojibake guards. The stable entrypoint writes `project_docs_readability.*`
outputs; the old `v1131` wrapper keeps `project_docs_readability_v1131.*`
only as a compatibility behavior.

The stable maintainer script map lives in `docs/script-entrypoints.md`. It
separates current engineering checks from historical and versioned scripts so
normalization work can improve the active path without pretending every old
experiment runner is already a maintained command.

The first shared report-writer extraction is in place through
`minigpt.reports.utils.write_output_bundle`. Active engineering report writers
use that owner path when they are not part of the lower-level reports package
initialization chain; `readability_report_artifacts.py` remains on
`minigpt.report_utils` to avoid a package import cycle.

These tests prove the currently normalized surface. They do not claim that every
historical governance chain has been refactored.

## Next Actions

1. Keep migrating active scripts to owner packages in small batches. Leave
   route-specific and versioned historical scripts alone until an active
   consumer proves they need cleanup.
2. Split or deduplicate implementation modules only when a real owner boundary
   is clear. Do not turn compatibility packages into large implementation
   files.
3. Reduce pressure on `minigpt.__init__` after active callers use explicit
   owner imports. Shrink facade exports only in tested batches.
4. Continue extracting shared report writer helpers where repeated
   `_artifacts.py` modules share an output contract. Prefer
   `minigpt.reports.utils` for active report writers, but keep lower-level
   compatibility helpers on `minigpt.report_utils` when importing the reports
   package would create a cycle.
5. Continue separating facts, judgments, and recommendations in governance
   documentation. Governance evidence is not proof of production model quality.

## Stop Rules

Pause a normalization batch when it would require moving route-specific
historical chains, changing artifact schemas, weakening compatibility exports,
or editing generated evidence archives. Those changes need a separate focused
plan and stronger regression coverage.
