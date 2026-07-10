# Deep maintenance closeout: v1268-v1272

## Scope

This closeout covers five engineering-maintenance versions. It does not claim a
model-quality improvement and does not change training semantics, cached
experiment artifacts, `decide()` logic, or promotion decisions.

## Outcome matrix

| Area | Before | After | Durable proof |
|---|---:|---:|---|
| Duplicate tag CI | branch and tag could test one commit twice | one `main` push run; tags are suppressed | v1271 commit+tag produced one successful push run, `29061484360` |
| Staged ruff debt | 545 findings | 271 findings, zero new findings | shrink-only baseline update logic and static-analysis gate |
| CI hygiene ownership | 523-line mixed-responsibility entrypoint | 80-line recorded facade plus focused checks/summary/types | byte-identical canonical report parity in `f/1270` |
| Strict mypy scope | 16 targets | 20 targets | committed scope floor and zero diagnostics |
| File-size warnings | 22 | 21 | file-size ratchet; no unwaived hard-limit files |
| Governance JSON readers | nine target-local copies | zero target-local copies | 14 cumulative protected modules in `f/1271` |
| Handoff facade | 477 physical lines at v1270 | 413 physical lines plus 113-line guard component | focused guard tests, strict ruff and mypy |
| Active 0%-covered contract | 0/63 statements | 59/63 statements (93.65%) | three in-process orchestration and failure-contract tests |
| Whole-project coverage | 88.98% enforced floor | 91.06% measured | 90,861/99,778 lines across 1,381 files |

Line-count metrics use the preserved version evidence for the v1270 parity row
and physical `splitlines()` counts for the handoff row; they are not presented
as a reduction in total repository LOC.

## Verification

```powershell
python -m pytest -q -o cache_dir=runs/pytest-cache-v1272
python -m pytest tests/test_promoted_training_scale_seed_handoff_assurance_smoke_contract.py -q
python -B scripts/run_test_coverage.py --out-dir runs/test-coverage-v1272 --fail-under 88.98
python -B scripts/check_engineering_health.py --out-dir runs/engineering-health-v1272
git diff --check
```

- Full pytest at the v1271 maintenance snapshot: `3747 passed in 1058.47s`.
- New in-process assurance-contract tests: `3 passed`; focused module coverage
  is `93.65%` (`59/63`).
- Final CI-style unittest discovery: `3538` cases; line coverage is `91.06%`
  (`90,861/99,778`) against the unchanged `88.98%` floor.
- Final engineering health passes all nine checks: source encoding, docs
  readability, CI hygiene, ruff, mypy, honest measurement, artifact schema,
  file-size ratchet, A-track closeout, and the normalization sub-suite.
- Browser verification of the final coverage HTML has zero console errors or
  warnings.

The full pytest and CI discovery counts differ because pytest collects test
forms that stdlib unittest discovery does not. Both counts are retained rather
than merged into one ambiguous total.

## Remaining debt

- The 271-entry ruff baseline remains visible. It is a ceiling, not a quality
  claim, and future updates may only shrink it.
- Twenty-one Python files remain above the 500-line warning threshold; eight
  historical tests above the 800-line hard limit have explicit no-growth
  waivers.
- The broad loader census still finds 496 historical files with a similar JSON
  reading shape. These are not bulk-migrated because many belong to frozen
  versioned science experiments.
- Full-suite verification takes roughly 17 minutes per discovery mode. A future
  test-runtime effort should first profile slow tests and prove equivalent
  discovery, not remove coverage for speed.

## Stop decision

The maintenance batch stops at v1272. The project now has stronger ratchets,
smaller active ownership surfaces, a tested shared-reader contract, and current
full-suite evidence. Further maintenance should be triggered by a real warning,
an active-file growth event, a new static finding, or a production requirement;
it should not continue as version-count-driven cleanup.
