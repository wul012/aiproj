# CI Execution Economy

This policy keeps the existing CI quality gates while avoiding work that cannot
produce additional confidence.

## Trigger policy

The primary workflow runs for:

- pushes to `main`;
- pull requests.

Tag pushes do not start a second workflow. A release tag points at the same
commit that was already verified by the `main` push, so rerunning the complete
suite for that tag would duplicate compute without testing different source.

## Dependency cache

`actions/setup-python` owns the pip cache. `requirements.txt` is the explicit
cache dependency path, so dependency changes invalidate the cache while normal
source-only commits can reuse downloaded wheels.

## Superseded runs

The workflow concurrency key is scoped by workflow and Git ref. When a newer
commit arrives on the same ref, GitHub cancels the older in-progress run. Pull
requests and `main` remain isolated from one another because their refs differ.

## Mechanical enforcement

Run:

```powershell
python -B scripts/check_ci_workflow_hygiene.py --out-dir runs/ci-workflow-hygiene
```

The report fails unless all of these are present:

- main-only push scope;
- no tag-push trigger;
- pip cache plus `requirements.txt` invalidation;
- same-ref concurrency grouping;
- `cancel-in-progress: true`.

The execution-economy checks are additive. They do not remove, reorder, or
weaken source encoding, documentation, lint, type, evidence, file-size,
normalization, test, or coverage gates.
