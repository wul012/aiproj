# Publication Receipt Version Template

Use this template before adding a new publication receipt, contract check, index, or review version. The goal is to keep new versions readable without renaming the historical chain.

## Version Scope

- Version:
- Version kind: `receipt | contract-check | index | review | maintenance`
- Source artifact:
- Output directory under `f/<version>/解释`:
- Screenshot path under `f/<version>/图片`:
- New script path, preferably under `scripts/publication/`:
- New source module path:
- New test path:

## Required Files

- CLI script with a short publication alias.
- Source builder module.
- Artifact writer or shared readability output helper.
- Focused test file.
- Runtime JSON/CSV/text/Markdown/HTML outputs.
- `f/<version>/解释/说明.md`.
- Code explanation when behavior, governance, or maintenance logic changes.
- README and archive index updates.

## Boundary Statements

- State whether the artifact is lookup-only, plan-only, review-only, or promotion-blocking.
- Keep `promotion_ready=False` and `approved_for_promotion=False` when the version does not prove model production readiness.
- Keep model quality claims bounded unless a real model capability validation says otherwise.
- Do not treat receipt chain consistency as training improvement.

## Verification

- `python -m py_compile` for new modules, scripts, and tests.
- Focused pytest for the new behavior.
- Real CLI run against repository evidence, not only fixtures.
- Source encoding hygiene.
- `git diff --check`.
- Browser screenshot for HTML reports when the version writes HTML evidence.

## Evidence Archive

- Put runtime outputs under `f/<version>/解释/<report-name>/`.
- Put the screenshot under `f/<version>/图片/`.
- Add or update the stage-specific explanation README.
- Keep old evidence directories in place; do not migrate historical artifacts without an explicit migration version.
