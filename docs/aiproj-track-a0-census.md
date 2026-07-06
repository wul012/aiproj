# aiproj A0 Census And Quick Wins

This document closes A0 from `docs/production-excellence-aiproj-brief.md`.
It records only fresh facts and small freshness fixes. It does not alter the
model-capability lane, cached experiment semantics, or any existing verdict.

## Scope

A0 asks for three things:

1. record what CI actually runs and confirm it is green on HEAD;
2. add a warning-only archive + `runs/` inventory;
3. check README/START_HERE freshness against the current version line and keep
   the educational/no-promotion boundary intact.

## CI Reverification

Latest green main run checked at A0 start:

- workflow: `ci`
- branch: `main`
- conclusion: `success`
- run id: `28743564518`
- commit: `d70ac204defc450dd2eb5f60302e5357c8ab5e2d`
- title: `v1259 review route promotion release readiness receipt index`
- URL: `https://github.com/wul012/aiproj/actions/runs/28743564518`

The workflow currently runs these steps:

| order | CI step |
|---:|---|
| 1 | checkout |
| 2 | setup Python 3.11 |
| 3 | install `requirements.txt` |
| 4 | source encoding and syntax check |
| 5 | project docs readability check |
| 6 | CI workflow hygiene check |
| 7 | archived path portability check |
| 8 | promoted seed handoff assurance smoke |
| 9 | promoted seed receipt contract failure smoke |
| 10 | promoted seed receipt contract failure smoke plan check |
| 11 | tiny scorecard comparison inline check smoke |
| 12 | CI tiny scorecard plan digest check |
| 13 | baseline candidate threshold boundary gate check |
| 14 | baseline candidate threshold boundary gate plan check |
| 15 | release readiness drift contract smoke |
| 16 | normalization guard |
| 17 | coverage-producing unit tests with `--fail-under 80` |

`pyproject.toml` still has pytest configuration but no ruff, black, or mypy
tooling. That is expected at A0; static analysis begins in A1.

## Test And Archive Census

Fresh local counts at A0 start:

| item | count / size |
|---|---:|
| test files under `tests/` | `725` |
| `a/` | `12.2342 MB`, `186` files |
| `b/` | `16.1532 MB`, `232` files |
| `c/` | `83.1583 MB`, `1599` files |
| `d/` | `38.8131 MB`, `2294` files |
| `e/` | `224.7105 MB`, `9080` files |
| `f/` | `14.9315 MB`, `778` files |
| archive total | `390.0008 MB` |
| `runs/` | `11.349 MB`, `155` files |

The committed inventory command is:

```powershell
python -B scripts/check_archive_runs_inventory.py --out-dir f/1260/解释/archive-runs-inventory --force
```

It produced `status=pass`, `decision=archive_runs_inventory_recorded`,
`warning_only=True`, and `warning_count=0`. The HTML screenshot is archived at
`f/1260/图片/archive-runs-inventory-v1260.png`.

## Freshness Fixes

`START_HERE.md` previously pointed readers to v1098-v1099 documentation-template
work. A0 updates it to the current v1260 production-excellence census line and
keeps the model-quality boundary explicit: governance evidence and capability
experiments remain educational unless a cited artifact says otherwise.

The root README and `docs/README.md` now link this A0 census, the archive
inventory rule, and the production-excellence brief. This is an index/freshness
fix only.

## Boundary

A0 did not:

- change any ML capability verdict;
- re-run training;
- move archive roots;
- promote a checkpoint;
- add ruff, black, mypy, or coverage ratchet changes.

Those are later A-track items.
