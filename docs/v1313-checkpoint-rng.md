# v1313 Checkpoint RNG reproducibility

## Task and baseline

User scope: archive the first two interview lessons in a new folder and deliver one aiproj engineering version.
Baseline `6e50c921` / CI `34171296812` passed. Latest implementation tag is `v1308.0.0`;
v1309-v1312 are later design records, so this new engineering cut uses `v1313.0.0` without changing package `0.1.0`.
The v1312 archive experiment remains blocked; no archive migration, floor reduction, science verdict or cache edit.
Existing personal untracked files are unrelated and must not be staged. No subagents are used.

## Family design

- Abstraction: `training.rng_state` captures/restores stochastic runtime state, not model semantics.
- Data boundary: an optional versioned `rng_state` checkpoint field carries Python/NumPy/Torch CPU and initialized CUDA state.
- Behavior boundary: train.py restores after setup; capture occurs at the continuation boundary before terminal sampling.
- Timing boundary: a final-only evaluation must not consume the state used for resumed training; scheduled evaluations stay unchanged.
- Test boundary: helper tests and actual tiny train/resume tests share data but not production decision logic.
- Compatibility boundary: missing RNG fields retain the legacy seed-based resume path; root exports and archived formats stay untouched.

## Requirement evidence matrix

| Requirement | Implementation | Failing check | State |
| --- | --- | --- | --- |
| Save lessons | `面试讲解_吴林东/` with index + two lessons | UTF-8, nonempty chapters and resolved local links | passed |
| Deterministic continuation | optional checkpoint RNG state | full training vs resumed training exact parameters/optimizer comparison | passed |
| Non-aligned stop + sampling | capture before final-only evaluation and sample | stops 1/2/3/5 with dropout 0.2 | passed |
| Backward compatibility | missing RNG field is accepted | old checkpoint still resumes | passed |
| CPU portability | CPU RNG tensors restored on CPU | serialization + CPU state check; CUDA mocks for uninitialized device | passed; CUDA hardware not tested |
| Preserve gates | existing source, tests, fixtures, floors unchanged except scoped additions | 21 fast CI commands + 3,585 tests / 89.26% against floor 88.98 | passed locally |
| Release one version | explicit staging, normal commit/tag/push | remote SHA and same-SHA CI | local record; remote receipt is the annotated release tag |

## Validation and failure conditions

Use CPU-only tiny generated text in TemporaryDirectory; no user training run is overwritten.
Run focused tests against the old implementation first, then against the new one, with identical assertions.
Exact training equivalence is scoped to unchanged data, tokenizer, hyperparameters, evaluation schedule,
same deterministic CPU environment and step-boundary checkpoints. No cross-device/version bitwise promise.
Scheduled diagnostic calls retain the existing RNG consumption, so uninterrupted training is not redefined.
Old checkpoints cannot recover a missing random sequence. A checkpoint taken after terminal reporting
contains a continuation snapshot, not necessarily the live process's post-sampling RNG position.

Failure: changed archived verdict/fixture/test expectations, diluted floor, CUDA initialized by a CPU-only
snapshot, wrong checkpoint timing, nonzero fast-gate/full-coverage result, or unintended staged personal file.
Write the walkthrough before final verification. Record commands/results before final handoff; stop after this version.

## Local evidence and reproducibility

- Focused command: `python -B -m unittest tests.test_rng_state tests.test_resume_rng tests.test_model_cli_behavior tests.test_architecture_boundaries -v`: 23 tests, OK.
- Old implementation failed all four stop-step subcases (1/2/3/5); the same assertions pass after the fix.
- Independent CLI processes: CPU, dropout 0.2, stop 3, target 6. Model tensors, optimizer state, final loss and sample
  exactly match uninterrupted training. The baseline uninterrupted implementation also retains identical weights,
  optimizer, metrics bytes and sample bytes. This is implementation reproducibility, not model-quality improvement.
- Full unchanged coverage entrypoint: `python -B scripts/run_test_coverage.py --out-dir .tmp/v1313/final-coverage --fail-under 88.98`:
  `Ran 3585 tests in 818.649s`, `OK`, `status=pass`, `line_coverage_percent=89.26`, exit 0.
  Measured 89,517 / 100,288 lines in 1,682 files. This keeps the existing mixed-corpus coverage scope; it does not
  resolve the distinct maintained-code coverage debt documented by v1312.
- All 21 existing fast CI commands passed, including strict lint/format, scoped type analysis, naming, schema,
  honest-measurement, size, elegance, smoke-plan checks and normalization guard. No threshold/baseline was relaxed.
- Machine evidence: `f/1313/解释/checkpoint-rng.json`; Chinese walkthrough:
  `代码讲解记录_工程保养阶段/1266-v1313-checkpoint-rng.md`.

## Deviations and closeout limits

- The first background coverage run ended without a final status. Its partial log was not counted as a pass;
  a separate fresh coverage database and complete exit record were required for the successful rerun.
- Ruff, mypy and coverage were missing from the local environment. They were installed only under task-local
  `.tmp/v1313/tools`; project dependency declarations were not edited.
- The initial relocated baseline CLI needed the repository root on PYTHONPATH. Only the temporary comparison
  harness was corrected; the archived baseline script bytes and production code were unchanged.
- No new screenshots: this change has no visual runtime surface; exact state/byte comparisons are stronger evidence.

## Publication receipt

This committed document records local verification; it does not predict a future CI result.
The annotated `v1313.0.0` tag is created only after the pushed implementation SHA passes CI.
Its message records the immutable implementation SHA, successful same-SHA CI URL and local gate summary.
This avoids a self-referencing commit hash or a permanently stale pending-CI row in committed evidence.

```powershell
git show --no-patch v1313.0.0
git ls-remote origin refs/tags/v1313.0.0 'refs/tags/v1313.0.0^{}'
gh run list --workflow ci.yml --commit (git rev-parse 'v1313.0.0^{}') --json databaseId,headSha,status,conclusion,url
```
