# v1315 Tokenizer identity binding

## Step-0 and scope

HEAD and origin/main are `f1bc2559aa201c406d5554116118e0b5149dbe48`, tagged v1314.0.0.
Same-SHA CI 34378188016 succeeded; task scratch v1314 is absent and the personal untracked
file set is unchanged. No active cross-project program is being resumed. This is one aiproj
engineering version; package version stays 0.1.0. No subagents.

CodeGraph context/explore was consulted first. Its tokenizer index points at the old forwarding
shim, so the live core implementation was checked. load_resume_state checks vocabulary size only:
a same-size ID permutation can silently reinterpret checkpoint embedding/output rows.

## Family design (before implementation)

- Abstraction: training.tokenizer_binding binds a checkpoint to supported tokenizer semantics.
- Data: optional tokenizer_sha256 checkpoint field, derived from a versioned canonical payload.
- Semantics: tokenizer kind, ordered vocabulary, unknown token and ordered BPE merge rules.
- Behavior: validate after tokenizer load, before model creation, training and output writes.
- Compatibility: absent field retains legacy loading; present malformed or different binding fails.
- Tests: shared table of semantic mutations, serialization roundtrips and real fail-before-write resume.
- Exclusions: no tokenizer format migration, signature/authenticity claim, data/config guard or inference migration.

## Requirement-evidence matrix

| Requirement | Implementation | Failing check | State |
| --- | --- | --- | --- |
| Reject same-size tokenizer mismatch | optional digest + loader check | swapped vocabulary IDs cause ValueError | passed locally |
| Bind BPE behavior, not just vocabulary | canonical ordered merges | changed merge order with same IDs is rejected | passed locally |
| Ignore irrelevant file presentation | fingerprint loaded semantic fields | JSON whitespace/key order and path changes still load | passed locally |
| Preserve old artifacts | absent digest follows existing behavior | legacy real checkpoint remains loadable | passed locally |
| Fail before side effects | validation in load_resume_state | recursive output bytes unchanged; destination not created | passed locally |
| Preserve correct continuation | unchanged RNG/save timing | prior resume RNG and checkpoint I/O suites | passed locally |
| Keep gates | unchanged floors and fixtures | all fast CI commands + full coverage >=88.98 | passed locally |
| Release one version | explicit staging + annotated v1315.0.0 | same-SHA remote CI and tag receipt | release receipt |
| Cleanup | remove task-owned scratch only | no scratch/helper process; original personal files intact | before handoff |

## Failure conditions and boundaries

Any relaxed baseline/floor, edited legacy fixture/assertion, hidden mismatch, file writes before rejection,
or unrelated staged document blocks delivery. Do not mistake negative test stdout for suite failure;
use command exit + unittest terminal summary + the coverage report's own summary.

The fingerprint detects accidental pairing errors, not malicious edits to both files or untrusted pickle.
It does not verify source data, evaluation schedule, optimizer configuration or cross-device determinism.
The existing inference entrypoints are not migrated this version. Legacy checkpoints cannot prove a
binding they never stored. Successful new saves add the binding; no historical checkpoint is rewritten.

## Publication receipt

Committed evidence records local facts. Create annotated v1315.0.0 only after origin/main matches the
implementation SHA and same-SHA CI succeeds; record the observed CI URL in its annotation.

## Strongest review question

Does a hash of tokenizer.json reject harmless formatting changes and still miss BPE rule order?
That would be the wrong abstraction: tests must prove semantic roundtrip stability and merge-order sensitivity.


## Local verification receipt

- Red control: the old loader accepted a same-size vocabulary ID swap; the unchanged assertion failed.
- Final focused command: 31 unittest cases passed in 15.692s, including char/BPE semantic binding,
  save-failure protection, exact RNG continuation, model CLI behavior and architecture boundaries.
- Full original coverage command: `Ran 3593 tests in 1022.269s`, `OK`, exit 0; report status pass.
  Coverage is 89.26% (89,552 / 100,323 lines, 1,684 files), with the unchanged 88.98% floor.
  `tokenizer_binding.py` is 100% covered. This remains the repository's mixed-corpus metric.
- All 21 fast CI commands exited 0, including strict static analysis/type checks and normalization.
- No scientific code, cached verdict, fixture, package version, coverage floor or baseline was changed.
