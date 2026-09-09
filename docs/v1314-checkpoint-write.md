# v1314 Checkpoint write isolation

## Scope and Step-0

One engineering version after `e6370cd313bff46c67695f81b012ab09c715945d` / `v1313.0.0`.
Local HEAD and origin/main match; same-SHA CI `34370872942` succeeded. The v1313 temporary
directory has been removed and the 14 pre-existing personal untracked files are unchanged.
CodeGraph was consulted first; its tokenizer paths are stale, so live train.py is authoritative.
The train entrypoint still calls torch.save directly on checkpoint.pt, risking the previous
checkpoint when serialization fails after truncating its destination.

## Family design (before implementation)

- Abstraction: `training.checkpoint_io.save_checkpoint` owns single-file publication only.
- Data: the existing checkpoint dictionary and torch serialization format stay unchanged.
- Behavior: unique same-directory temporary file, serialize, flush, fsync, close, os.replace.
- Cleanup: remove only this invocation's temporary file when Python unwinds, including interrupts.
- Tests: a data-driven failure matrix plus real train/fail/resume integration, no existing fixture edits.
- Exclusions: no experiment, RNG schedule, tokenizer transaction, manifest schema or dependency changes.

## Requirement-evidence matrix

| Requirement | Implementation | Failing evidence gate | Status |
| --- | --- | --- | --- |
| Preserve the previous checkpoint on failure | isolated write then replace | old file bytes and torch.load survive each injected failure | passed locally |
| Complete first save or no checkpoint | same publication helper | absent target remains absent after a failed write | passed locally |
| Clean temporary files on handled failures | finally cleanup, including KeyboardInterrupt | directory inventory unchanged except successful checkpoint | passed locally |
| Real entrypoint uses the helper | train.py call site | train/fail/retry reads a valid old checkpoint | passed locally |
| Writer dies before publication | isolated incomplete candidate | kill a child after a partial write; old file still loads | passed locally |
| Preserve v1313 continuation | checkpoint payload/RNG timing unchanged | existing exact full-versus-resume tests | passed locally |
| Keep quality gates | no floor/baseline changes | every fast CI command and full unchanged 88.98 coverage floor | passed locally |
| One release | explicit staging and annotated v1314.0.0 tag | remote SHA and same-SHA CI | release tag receipt |
| Cleanup | task-local scratch only | path absent, original untracked set unchanged, no task helper process | before handoff |

## Failure conditions and boundaries

Any modified legacy expectation/fixture, relaxed ratchet, swallowed save exception, truncated old
checkpoint, leaked temporary file during normal unwinding, or unintended staged file blocks release.
Write the Chinese walkthrough before final verification; use the same red/green assertions.

This is not a transaction across checkpoint, tokenizer, metrics, sample and manifests. Diagnostics
may already have advanced when checkpoint saving fails. It does not add writer locking, checkpoint
rotation, automatic orphan deletion or power-loss durability of the directory entry. A hard kill
can leave a temporary file; tests must not turn ordinary exception cleanup into a SIGKILL claim.
The parent directory must already exist. Filesystem replace semantics remain a runtime prerequisite.

## Publication receipt

The committed report records local verification, not a future remote result. Create the annotated
`v1314.0.0` tag only after origin/main matches the implementation SHA and same-SHA CI succeeds.
The annotation carries the observed CI URL and immutable commit, avoiding a self-referencing receipt.

## Deviations and strongest review question

Strongest question: does a tiny successful-save test prove that
an interrupted save preserves the old model? No: the failure matrix and real train/fail/retry path
are required, alongside an explicit distinction between exception unwinding and abrupt process death.

The first draft of the red test reused a tiny dataset with the default 90/10 split, leaving too few
validation tokens. That input error was not counted as a regression reproduction. Before touching
production, the test selected a 50/50 split (without changing fixture bytes) and then failed specifically
because the old checkpoint was replaced by `incomplete checkpoint`. The same assertion is used after the fix.

The temporary CI wrapper twice confused nested test output with the enclosing run's result: first
normalization sample output (`ready`), then intentional failure-case output in full coverage (`fail`).
Neither is the test-run verdict. Actual coverage exited 0, unittest reported 3,590 tests / OK, and the
coverage report's own summary passed. The raw wrapper error remains recorded as an aggregation error;
it is not relabeled a successful wrapper run. This repeated result-ownership mistake was promoted to
AGENTS.md. The fixed wrapper uses exit codes, unittest terminal summaries and each gate's own result;
no product test, fixture, floor or baseline changed. A fresh fast sweep runs before commit.

## Local verification receipt

- Focused unittest command in `f/1314/解释/checkpoint-write.json`: 28 tests, OK (9.939s).
- Full original coverage command: 3,590 tests, OK (857.589s); command exit 0, report status pass.
  Coverage 89.26% (89,533 / 100,305 lines, 1,683 files), unchanged floor 88.98%.
  New checkpoint_io module: 17 / 17 executable lines covered. This is the existing mixed-corpus
  metric, not a claim that the maintained-code coverage debt is resolved.
- All 21 fast CI commands rerun with result ownership fixed: exit 0, each top-level gate passed;
  normalization's own unittest summary is OK (the nested ready artifact is not the gate verdict).
- New helper passes strict mypy; changed source/test pass ruff lint and new-module format checks.
- Source payload keys and RNG timing remain unchanged; production growth is 31 helper lines plus
  one import/call-site replacement. No scientific code, existing fixture or ratchet baseline was edited.
- Reproduction details and output summaries: `f/1314/解释/checkpoint-write.json`.
  Walkthrough: `代码讲解记录_工程保养阶段/1267-v1314-checkpoint-write.md` (3,432 Chinese characters).
