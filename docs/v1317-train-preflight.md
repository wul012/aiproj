# v1317 Training preflight

## Step-0 and scope

Baseline: `abe55c5ac44eeecde4e7e401b053bc9f144c4b99`, main/origin/tag v1316.0.0;
CI 34474412901 succeeded. The 14 personal untracked root files are unchanged, and interview
notes remain ignored/local-only. CodeGraph was queried first; common parse_args names produced
ambiguous results, so the specific live train.py/core.dataset/core.model files were checked.
One engineering version, no subagents, no scientific experiment or cached verdict changes.

## Family design (before implementation)

- Abstraction: training.preflight validates effective CLI options and batchable split sizes.
- Data: numeric constraints are small name/bound tables; no second parser/default configuration.
- Behavior: pure validation, no filesystem writes, random draws, model construction or hidden repair.
- Timing: option checks immediately after parsing; split checks before model creation/history recovery.
- Compatibility: ignored model/BPE options on resume and sample options under --no-sample stay ignored.
- Boundaries: preserve zero learning rate, zero new sample tokens and the existing batch-size threshold.
- Tests: table-driven invalid inputs plus real fresh/resume output preservation and valid-path parity.

## Requirement-evidence matrix

| Requirement | Implementation | Failing evidence | State |
| --- | --- | --- | --- |
| Reject invalid work before output changes | option preflight | fresh-run invalid eval/sample options preserve old output bytes | passed locally |
| Reject unbatchable data before deleting history | split-size preflight | old metrics remain when train/validation split is too small | passed locally |
| Protect recovery evidence on invalid resume | preflight before recovery | uncommitted suffix and original run files unchanged on rejection | passed locally |
| Reject non-finite floating options | finite range checks | NaN/Infinity rejected; legitimate boundaries accepted | passed locally |
| Keep inactive options inactive | conditional checks | no-sample and checkpoint-owned architecture options remain accepted | passed locally |
| Preserve valid model behavior | no RNG/algorithm/default changes | previous 40 focused cases plus independent baseline parity | passed locally |
| Preserve release gates | original tests/fixtures/floor unchanged | 21 local fast gates and same-SHA full CI >=88.98 | before release |
| Release one version | explicit paths and tag after success | remote SHA/tag/CI plus scratch and process cleanup | before handoff |

## Failure conditions and verification route

No changed old assertion/fixture, new dependencies, silent value clamping or relaxed baseline/floor.
An invalid request that changes run outputs or restores/truncates history is a failure. Existing
default arguments and accepted zero-value behavior must be tested, not generalized into >0 rules.
Write the walkthrough before final verification. Full validation uses the unchanged workflow command:
`python -B scripts/run_test_coverage.py --out-dir runs/test-coverage-ci --fail-under 88.98`.
Local focused/fast gates run first; full same-SHA GitHub CI must pass before tagging. This avoids
repeated interrupted local full runs documented by v1316 without reducing the release test scope.

## Explicit non-goals and review question

No new output overwrite policy, directory transaction, data fingerprint, optimizer schedule, generation
algorithm, resource quota, GPU experiment, inference CLI migration or tokenizer format change.
The existing small-validation fallback and get_batch minimum are preserved, not silently fixed.
These checks prevent known deterministic input errors; they cannot preclude later OOM, disk failure,
external file changes or non-finite gradients. Failed requests may still read inputs and valid-option
data checks follow seeding; only pure option rejection is guaranteed to precede RNG initialization.

Strongest objection: validation may reject options that are ignored on resume or no-sample. Tests must
prove those controls still use the saved model configuration and skip disabled sampling checks.
Local evidence is committed without predicting future CI; the annotated release tag records the
actual full-run result and immutable target SHA after success. No extra receipt commit is required.


## Local evidence

- Red control against v1316: two failures, specifically missing rejection and lost metrics bytes.
- Final focused invocation: 49 tests in 20.006s, OK, exit 0. New module's 9 tests include 33 invalid
  option subcases; existing resume, history, checkpoint, tokenizer, model CLI and architecture tests pass.
- Independent three-process check against v1316: full checkpoint data equal; metrics, summary,
  sampling and tokenizer bytes equal. Invalid CLI exits nonzero and leaves all previous outputs unchanged.
- Strict mypy and ruff/format checks pass. Full command and thresholds are unchanged; no old test
  assertions/fixtures or scientific source were edited. Existing completed v1316 CI is not counted as v1317.
- Machine evidence: `f/1317/解释/train-preflight.json`. Walkthrough:
  `代码讲解记录_工程保养阶段/1270-v1317-train-preflight.md` (3,227 Chinese characters).
