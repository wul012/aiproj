# v1318 RNG snapshot validation before restoration

## Step-0 and scope

Baseline main/origin/tag v1317.0.0: `dc8cd56f9680bd81f2ab3e8822b60ad9d20f4905`.
CI 34671490205 succeeded. Personal untracked files are unchanged; interview notes remain local-only.
CodeGraph context/explore located load_resume_state; its live source and rng_state helper were checked.
Current restoration mutates Python before validating NumPy/Torch, and train restores RNG only after
history recovery/output preparation. An invalid snapshot can therefore cause partial side effects.
One engineering version, no subagents or scientific experiment/fixture/dependency changes.

## Family design (before implementation)

- Reuse training.rng_state: validation and normalization precede restoration; no new RNG format.
- Data: existing version 1 Python/NumPy/Torch CPU and optional CUDA snapshot fields.
- Behavior: private generator probes validate CPU payloads without touching global generators.
- Timing: loader validation before model/output/history effects; real restoration keeps its old boundary.
- CUDA boundary: structural validation/CPU normalization only; no device initialization or GPU replay claim.
- Tests: table-driven malformed snapshots, global-state preservation, actual loader/CLI rejection and parity.

## Requirement-evidence matrix

| Requirement | Implementation | Failing gate | State |
| --- | --- | --- | --- |
| Reject invalid RNG before history/output changes | validate on checkpoint load | invalid saved RNG leaves complete run bytes unchanged | passed locally |
| No partial global state from malformed CPU snapshots | validate via private generators | invalid NumPy/Torch state does not mutate Python/NumPy/Torch globals | passed locally |
| Normalize before setters | prepared snapshot | Tensor state on CPU, same successful replay sequence | passed locally |
| Preserve legacy compatibility | absent/None state no-op | legacy fixtures and resume tests unchanged | passed locally |
| Preserve CUDA boundary | structure check only | no CUDA runtime init; existing mocked restore tests pass | passed locally |
| Valid trajectory unchanged | capture format and restore timing unchanged | existing focused regression and independent v1317 parity | passed locally |
| Maintain release quality | local fast/scoped checks + full same-SHA CI | unchanged 88.98 coverage gate | before tag |
| Finish exactly one version | explicit stage/push/tag/cleanup | original personal files and local notes unchanged | before handoff |

## Failure conditions and verification

No changes to old assertions, fixtures, baseline/floors, model algorithm or sampling order. Any mutation
of existing output on malformed RNG rejection, or global RNG during validation, is a failure. Write the
walkthrough before final verify. All 21 fast gates run locally; full unittest/coverage must pass in the
same-SHA GitHub checkout before the annotated v1318.0.0 tag. Do not prefill a future full-run result.

## Boundaries and strongest review question

This guards accidentally malformed saved state, not malicious pickle or authentic provenance. Private
CPU generators validate the installed libraries' accepted format, not mathematical quality. CUDA bytes
receive structural checks only; device-count, driver/runtime state validity and unexpected native setter
failures are not a transactional guarantee. Actual training main still seeds globals before loading the
checkpoint; the no-mutation promise applies to the validator/failed helper restoration, not the whole CLI.
Existing explicit None/missing RNG state remains legacy no-op. Cross-version/device determinism is not promised.

Strongest objection: validating by calling global setters and rolling back could leak state mid-check.
Use isolated generators instead, then verify globals and saved payload stay unchanged, and keep successful
restoration at the original post-setup step boundary. No duplicate serialization or CUDA startup is needed.

## Development deviations

The first malformed-payload matrix found that random.Random.setstate(()) raises IndexError, not
ValueError. Exception normalization now includes LookupError (covering missing keys and empty
sequence indexing); the same test assertion remains unchanged. This was a local pre-release failure,
not counted as a pass. No historical test or fixture changed.


## Local verification receipt

- Red control: two regression assertions fail against v1317; same assertions pass after the fix.
- Final focused command: 55 tests, 19.338 seconds, OK, exit 0; new tests include 21 malformed snapshots.
- Strict mypy, lint and format checks pass; capture_rng_state AST and historical test/fixture files unchanged.
- Independent four-process parity includes the old train.py AND old RNG helper: complete checkpoint data,
  metrics, sample, summary and tokenizer match; invalid resume rejects without file changes.
- Machine record: `f/1318/解释/rng-validation.json`. Public engineering walkthrough:
  `代码讲解记录_工程保养阶段/1271-v1318-rng-validation.md` (3,205 Chinese characters).
- Full same-SHA CI is required before tagging; the tag carries the observed count/coverage and CI URL.
