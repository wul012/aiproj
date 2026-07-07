# Start Here: MiniGPT From Scratch

## What this project does

This repository is a PyTorch learning project for building, training,
inspecting, and evaluating a small GPT-style language model from scratch.

It covers the full local learning path:

```text
tokenizer -> dataset -> transformer model -> training -> generation -> inspection -> evaluation -> reports
```

The project also keeps detailed versioned notes, screenshots, reports, and
evidence archives so each stage can be reviewed later.

## Why it matters

This is not only a toy model repo. It is a structured AI engineering practice
project.

The strongest parts are:

- A clear MiniGPT model learning path.
- Local evaluation and benchmark tooling.
- Dataset, experiment, model-card, release-readiness, and maturity-report
  evidence.
- Versioned documentation that explains what changed and why.

For a reader, the main value is seeing how a small model project can grow from
basic training into a more disciplined evaluation and release workflow.

## How to run it

Start by reading the main `README.md`, then inspect the current architecture
and workflow docs under `docs/`.

Typical workflow:

```powershell
python -B scripts/check_engineering_health.py
python -B scripts/check_static_analysis.py --out-dir runs/static-analysis
python -B scripts/check_type_analysis.py --out-dir runs/type-analysis
python -m unittest discover -s tests -v
python -B scripts/run_test_coverage.py --out-dir runs/test-coverage --fail-under 88.98
python -B scripts/check_normalization_guard.py
python -B scripts/check_archive_runs_inventory.py --out-dir runs/archive-runs-inventory --force
```

Use the first command for the current maintainer health check. Use the static
analysis command when changing Python source or scripts; it compares ruff
findings against the committed baseline and keeps strict paths format-clean.
Use the broad unittest command when you need full test discovery, and the
coverage command when you need the same thresholded unit-test entrypoint used by
CI. Use the normalization guard when you are changing architecture boundaries,
owner-package imports, public API surfaces, repository hygiene, or project
documentation. Use the archive/runs inventory when checking evidence growth; it
is warning-only and does not move archive roots.

For specific training, evaluation, dashboard, or report commands, use the
matching section in `README.md` because the project has many versioned
workflows.

## Top technical highlights

1. **MiniGPT model core**
   - Tokenizer, causal self-attention, training, generation, and prediction
     inspection.

2. **Evaluation discipline**
   - Fixed prompt suites, generation-quality reports, benchmark scorecards,
     comparison reports, and maturity narratives.

3. **Evidence-first workflow**
   - Versioned screenshots, report artifacts, code explanations, and
     release/readiness gates make the project easier to audit.

## Latest version summary

Current README focus: **v1263 production-excellence A2 coverage ratchet**.

v1263 completes A2 by raising the CI coverage floor to `88.98`, derived from
the v1262 measured `90.98%` baseline minus two points. The floor is written in
`docs/static-analysis/coverage-floor.json`, mirrored by CI workflow hygiene,
and checked by project-configuration tests. This is an engineering-maintenance
gate, not a model-quality promotion: model capability claims remain educational
unless tied to cited evidence, and governance `status=pass` still does not
imply production model readiness.

## Where to look next

- `README.md` - full project overview and version map.
- `docs/architecture-map.md` - current owner-package architecture map.
- `docs/module-inventory.md` - module ownership and compatibility inventory.
- `docs/public-api.md` - public API tiers and migration rules.
- `docs/engineering-workflow.md` - standard local and CI checks.
- `docs/normalization-guard.md` - focused guard modules and what each protects.
- `docs/script-entrypoints.md` - stable maintainer scripts and historical script boundary.
- `docs/static-analysis.md` - staged ruff baseline and scoped mypy gate.
- `docs/archive-runs-inventory.md` - warning-only archive and `runs/` growth inventory.
- `docs/aiproj-track-a0-census.md` - A0 production-excellence census evidence.
- `docs/aiproj-track-a1-static-analysis.md` - A1 static-analysis adoption evidence.
- `docs/aiproj-track-a2-coverage.md` - A2 coverage-floor ratchet evidence.
- `docs/production-excellence-aiproj-brief.md` - Claude-authored A-track execution brief.
- `文档分流说明.md` - current documentation routing map.
- `src/minigpt/` - model, evaluation, reporting, and workflow code.
- `tests/` - behavior, contract, configuration, and boundary tests.
- `e/` - v473-v1097 runtime screenshots and explanations.
- `f/` - v1098+ runtime screenshots and explanations.
- `代码讲解记录_模型能力阶段/` - v473-v1097 historical explanations.
- `代码讲解记录_模型治理阶段/` - v1098+ model-governance explanations.
- `代码讲解记录_工程保养阶段/` - engineering maintenance and production-excellence
  explanations when a version needs a detailed walkthrough.
