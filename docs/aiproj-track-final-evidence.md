# aiproj A-Track Final Evidence

This document closes the production-excellence A-track from
`docs/production-excellence-aiproj-brief.md`. It is a review map for A0 through
A5, not a model-quality promotion. The model-quality boundary remains the one
defined in `docs/no-promotion-boundary.md`: governance evidence can prove that
an artifact is traceable, schema-valid, bounded, or CI-protected, but it does
not prove that a checkpoint is production ready.

## Final Status

| Item | Evidence |
|---|---|
| Latest completed A4 CI on `main` | `https://github.com/wul012/aiproj/actions/runs/28846542546` |
| Latest completed A4 CI on tag | `https://github.com/wul012/aiproj/actions/runs/28846544549` |
| Current closeout gate | `scripts/check_aiproj_track_closeout.py` |
| Current closeout module | `src/minigpt/aiproj_track_closeout.py` |
| Current closeout tests | `tests/test_aiproj_track_closeout.py` |
| Active no-promotion wording | `docs/no-promotion-boundary.md` |

## No-Promotion Boundary

The closeout keeps `docs/no-promotion-boundary.md` as the active source for
promotion wording. Any A-track pass means the engineering gate is present and
reviewable; it does not mean the model is production ready, promoted, or
stronger than the cited toy-scale evidence.

## Gate-By-Gate Evidence Matrix

| Track | Implemented Gate | Mechanical Failure Condition | Evidence And Docs | Boundary |
|---|---|---|---|---|
| A0 | Archive and `runs/` inventory plus freshness check | Archive inventory command fails or warning-only inventory cannot be regenerated | `scripts/check_archive_runs_inventory.py`, `docs/archive-runs-inventory.md`, `docs/aiproj-track-a0-census.md`, `f/1260/解释/archive-runs-inventory/` | Census only; no artifact relocation, no training, no promotion |
| A1 | Staged ruff gate | New ruff finding outside `docs/static-analysis/ruff-baseline.json`, strict path lint issue, or strict path format drift | `scripts/check_static_analysis.py`, `docs/static-analysis/ruff-baseline.json`, `docs/aiproj-track-a1-static-analysis.md`, `f/1261/解释/static-analysis/` | Maintained-path quality gate only |
| A1 | Scoped strict mypy gate | Scope shrinks below floor, target/group validation fails, or mypy diagnostics appear in the declared scope | `scripts/check_type_analysis.py`, `docs/static-analysis/mypy-scope.json`, `docs/aiproj-track-a1-static-analysis.md`, `f/1262/解释/type-analysis/` | Scoped type gate; not a full-repository type claim |
| A2 | Coverage floor ratchet | CI coverage command falls below `fail_under=88.98`, or workflow/policy/tests disagree on that floor | `scripts/run_test_coverage.py`, `docs/static-analysis/coverage-floor.json`, `docs/aiproj-track-a2-coverage.md`, `f/1263/解释/test-coverage/` | Test-quality ratchet only; no model-quality upgrade |
| A3 | Honest measurement gate | Registered capability family loses cached-artifact-only boundary, no-promotion fields, expected source fields, or positive/negative contract markers | `scripts/check_model_capability_honest_measurement.py`, `docs/model-capability-honest-measurement-registry.json`, `docs/aiproj-track-a3-honest-measurement.md`, `tests/test_model_capability_honest_measurement.py` | Claim-boundary and reproducibility guard only |
| A3 | Artifact schema guard | Registered card or publication receipt loses required fields, selected expected values, simple type shape, or no-promotion receipt fields | `scripts/check_artifact_schema_guard.py`, `docs/artifact-schema-guard-registry.json`, `docs/aiproj-track-a3-artifact-schema-guard.md`, `f/1265/解释/artifact-schema-guard/` | Artifact-envelope guard only |
| A4 | File-size ratchet | Unwaived Python file exceeds 800 lines, or a waived legacy oversize file grows above its baseline | `scripts/check_file_size_ratchet.py`, `docs/code-health/file-size-ratchet.json`, `docs/aiproj-track-a4-code-health.md`, `f/1266/解释/file-size-ratchet/` | Maintainability guard only; no contract-preserving split hidden in A4 |
| A5 | Final evidence and docs honesty closeout | This final evidence doc, no-promotion wording, README/docs indexes, A-track docs, or CI closeout wiring loses required citations | `scripts/check_aiproj_track_closeout.py`, `src/minigpt/aiproj_track_closeout.py`, `tests/test_aiproj_track_closeout.py`, `f/1267/解释/aiproj-track-closeout/` | Closeout/readiness map only; Stage 2 remains gated |

## Waiver List

The only A-track maintainability waivers are the eight A4 file-size waivers in
`docs/code-health/file-size-ratchet.json`. They are all legacy test files above
the hard 800-line line limit. The rule is no-growth, not permanent exemption:
if any waived file grows above its committed baseline, `scripts/check_file_size_ratchet.py`
fails.

| Waived File | Baseline Lines | Follow-Up Direction |
|---|---:|---|
| `tests/test_promoted_training_scale_seed_handoff.py` | 1398 | Split seed-handoff fixtures and assertion helpers before adding cases |
| `tests/test_promoted_training_scale_seed_handoff_receipt.py` | 1281 | Split receipt fixtures and negative-case helpers before adding cases |
| `tests/test_registry.py` | 944 | Split registry fixture construction by registry family |
| `tests/test_maturity_narrative.py` | 894 | Split maturity narrative fixtures from output/render assertions |
| `tests/test_release_readiness_comparison.py` | 873 | Split comparison fixtures from renderer assertions |
| `tests/test_promoted_training_scale_decision.py` | 838 | Split decision fixtures from failure-mode assertions |
| `tests/test_promoted_training_scale_seed.py` | 836 | Split seed plan fixtures from report assertions |
| `tests/test_server.py` | 815 | Split server route fixture setup from response assertions |

## Census And Ratchet Numbers

| Gate | Current Number |
|---|---:|
| Ruff historical baseline issues | 545 |
| Strict mypy target floor | 16 |
| Coverage observed baseline | 90.98 |
| Coverage fail-under floor | 88.98 |
| File-size warning line limit | 500 |
| File-size hard line limit | 800 |
| File-size waiver count | 8 |

## A5 Review Notes

- A0 docs were kept as historical A0-start evidence, but wording now says
  "At A0 start" where the workflow later changed during A1-A4.
- A1-A4 docs are linked from `README.md`, `docs/README.md`, and `START_HERE.md`.
- `scripts/check_aiproj_track_closeout.py` keeps this closeout doc indexed and
  checks that CI contains the A5 gate before the coverage-producing unit tests.
- `docs/no-promotion-boundary.md` remains the central wording reference for
  `promotion_ready=False`, `approved_for_promotion=False`, bounded
  `model_quality_claim`, and lookup-only governance use.

## Reviewer Handoff

Claude review should treat this as the A-track closeout packet. The reviewer
can rerun the mechanical gate with:

```powershell
python -B scripts/check_aiproj_track_closeout.py --out-dir runs/aiproj-track-closeout --require-pass
```

The expected result is `status=pass`, `decision=aiproj_track_closeout_ready`,
and `failed_check_count=0`. A pass here means the A-track evidence map is
complete and mechanically protected; it does not grant Stage 2 execution by
itself, and it does not promote model quality.
