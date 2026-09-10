# v1316 Checkpoint-bound history recovery

## Step-0 and scope

Baseline main/origin/tag v1315.0.0: `949d721de0449b735babc1e8c9e27e940c6f2bb8`.
CI 34424626555 succeeded. Previous scratch v1315 was removed (1,931 files / 80,380,182 bytes);
the 14 personal untracked files remain out of scope. CodeGraph was consulted; its history entry
points forward to core.history, whose live append/load behavior was checked. No active cross-project
program, science verdict, archived fixture or dependency declaration is changed. No subagents.

Closeout base is now `15dedf794b78fd27b34817afb0361bde87a51f06` / CI 34454533609 (success):
the intervening user-requested documentation removal is separate from this engineering version.
Personal interview notes remain local-only and ignored; this version does not reintroduce them.

## Family design (before implementation)

- Abstraction: training.history_recovery stamps a byte prefix and reconciles same-run history.
- Data: optional history_state with version, byte size and SHA-256; no metric value/format changes.
- Behavior: verify the committed prefix before writing; archive full original bytes before rollback.
- Reuse: extract checkpoint_io's existing atomic writer for both checkpoint and history publication.
- Reuse: the third tiny-resume test uses a shared argument builder in existing model_cli_fixtures.
- Compatibility: missing state and explicit resume into a different output directory keep prior behavior.
- Limits: single writer, file-sized memory, no directory transaction, retention policy or cross-run repair.

## Requirements and evidence

| Requirement | Implementation | Failing check | State |
| --- | --- | --- | --- |
| No duplicate failed-attempt metrics | checkpoint-bound history prefix | real train/save-fail/retry steps match successful path | passed locally |
| Preserve discarded evidence | content-addressed full-history backup | backup bytes equal pre-recovery bytes | passed locally |
| Reject altered committed data | prefix length/hash validation | tampered/truncated/missing history unchanged on error | passed locally |
| Recover even an incomplete suffix | raw byte prefix, not parsing uncommitted rows | partial UTF-8/JSON suffix archived and excluded | passed locally |
| Atomic/idempotent recovery | shared atomic writer | archive/write failures preserve original; retry succeeds | passed locally |
| Respect boundaries | same run only, optional metadata | legacy and alternate-output paths keep behavior | passed locally |
| Preserve previous work | unchanged RNG/tokenizer/checkpoint assertions | complete focused regression and full existing suite | focused pass; full result in release tag |
| Honest quality evidence | own report/terminal status, unchanged floors | all fast CI commands and coverage >=88.98 | local fast record; full result in release tag |
| One release and cleanup | explicit staging, tag after same-SHA CI | remote refs, scratch absent, no owned helper process | before handoff |

## DONE, failure conditions and review

Write the walkthrough before final verification. A changed old assertion/fixture/floor, swallowed
I/O error, silently discarded history, changed science result or unrelated staged file blocks release.
No global stdout status scan: use each command exit and its own report or unittest terminal summary.
The annotated v1316.0.0 tag is the remote receipt; committed evidence records only observed local facts.

Strongest objection: this could destroy edited logs while pretending to recover. Therefore prefix
identity is mandatory for new metadata, the entire original is backed up before replacement, and
backup conflicts or prefix drift fail before any change. A missing legacy marker proves nothing and
does not trigger repair. Only resuming beside the original checkpoint activates reconciliation;
forking into another output directory is not given synthetic historical provenance.

The marker does not authenticate a checkpoint, validate model quality or certify power-loss durability.
Recovery backups are retained user artifacts, not task scratch. History rewrites are limited to runtime
files explicitly selected by a resume invocation; this development task only runs temporary toy data.

## Deviations

- On continuation, the first full-coverage runner no longer existed and its log lacked a terminal
  summary/exit record; the stale running JSON was not counted as passed. Its 21 completed fast gates
  remain distinct evidence. A fresh database/output full rerun is required. The repeated interrupted
  verification pattern (also seen in v1313) is promoted to AGENTS.md, with PID-aware background recovery.
- Extracting the shared test arguments exposed two existing import-order lint errors in the touched
  fixture helper. Moving its redundant bootstrap call below imports resolves them without changing the
  existing checkpoint factory AST, argument values or assertions (checked against baseline).
- The independent local coverage retry also ended without a live process or final report after user
  continuation. Neither partial run counts as full validation. Closeout reruns local focused/fast checks;
  the unchanged full coverage command will run in a fresh same-SHA GitHub CI checkout. Publication stays
  blocked until that external full run succeeds. Its observed test count, coverage and URL go in the
  annotated release tag rather than a fabricated local result. No test selection or floor is weakened.
- A supplementary scoped coverage invocation exited with native code -1073741819 before any test output.
  Its cause is undetermined and it contributes no pass evidence. Ordinary focused unittest was rerun
  successfully with an explicit exit record; no production or test changes were made to conceal this failure.

## Local evidence and remote publication

The local red control produced steps `[2, 3, 3]` instead of `[2, 3]`. The unchanged assertion now passes.
The final focused invocation passed 40 tests (13.108s, exit 0), covering recovery plus prior checkpoint,
tokenizer, RNG, model CLI and architecture tests. Strict mypy passed for both touched production helpers.
An independent four-process experiment passed all nine checks: model and optimizer exact equality,
metrics and summary byte parity, matching committed-history marker, complete recovery backup and notification.
Original test assertions/argument values and tiny checkpoint factory AST were checked against v1315.

Machine evidence: `f/1316/解释/history-recovery.json`. Public engineering explanation:
`代码讲解记录_工程保养阶段/1269-v1316-history-recovery.md`. These do not include personal interview notes.
The existing full command is `python -B scripts/run_test_coverage.py --out-dir runs/test-coverage-ci --fail-under 88.98`.
No claim of a completed local full run is made. Inspect the annotated release tag for the observed full-run
test count, coverage and same-SHA CI link; no tag is created before success.
