# v1319 Training data binding

## Scope and Step-0

HEAD/origin/tag v1318.0.0 is `4e5d97990c99907d12d0a9e04b349bb0e4e763e9`; its same-SHA CI
34673043406 passed. Personal interview notes are local-only and ignored. This engineering version
does not alter science experiments, cached verdicts, model math, tokenizer format or dependencies.

v1315 binds tokenizer semantics and v1318 validates RNG payloads, but a resumed run can still receive
modified text with the same vocabulary. It also accepts a changed `train_ratio`, silently changing
the sampled train/validation tensors. The current checkpoint has no data identity field.

## Family design (before implementation)

- Abstraction: `training.data_binding` binds exact text content and split configuration.
- Data: optional version-1 object with UTF-8 text SHA-256, text length and `train_ratio`.
- Behavior: validate after loading text/checkpoint and before split/model/history/output mutations.
- Compatibility: absent field keeps legacy behavior; same content at another path remains valid.
- Semantics: hash loaded text, not raw file bytes/path/tokenizer IDs; existing newline and preparation rules stay.
- Reuse: existing preflight ratio validation and checkpoint dictionary; no second data loader.
- Tests: same-vocabulary mutation, ratio drift, formatting/path identity, legacy loading and full parity.

## Requirement-evidence matrix

| Requirement | Implementation | Failing check | State |
| --- | --- | --- | --- |
| Reject modified same-vocabulary text | text digest validation | changed text accepted by old loader | passed locally |
| Reject changed split ratio | ratio in binding | ratio drift accepted by old loader | passed locally |
| Avoid path coupling | content-only digest | identical text at a new path loads | passed locally |
| Preserve legacy artifacts | optional field | old checkpoint resumes without binding | passed locally |
| Fail before side effects | validation before split/output | existing history and output bytes unchanged | passed locally |
| Preserve valid continuation | unchanged RNG/tokenizer/model path | current focused suite and independent parity | passed locally |
| Keep quality gates | no floor/baseline/science changes | 21 fast gates and same-SHA full CI | before tag |

## DONE, boundaries and failure conditions

Any changed old assertion/fixture, modified science verdict, path-only identity, silent repair,
or output mutation before mismatch rejection blocks release. Raw text hashing does not authenticate
files, detect malicious checkpoint edits, validate optimizer/scheduler/evaluation settings or guarantee
cross-device determinism. Legacy checkpoints cannot prove data identity they never stored. Data-directory
ordering remains the existing prepared-dataset contract; this version does not redesign it.
Only missing binding fields are legacy; explicit null and malformed fields fail. Text length is in
characters, not tokens. Switching output directories does not waive this newly explicit same-data
resume contract. Intentional fine-tuning on changed data is outside this version; no override is added.

The local full suite is not required if the same-SHA GitHub workflow reports its own successful
unittest/coverage result; no future result is written into committed evidence before observation.
The walkthrough is written before final verification. The annotated v1319.0.0 tag carries the actual
remote receipt; temporary scripts/tools are removed after closeout.

## Local verification receipt

The old implementation red control failed because same-vocabulary text mutation was accepted.
The focused regression command covers
data binding, RNG validation, preflight, history recovery, checkpoint I/O, tokenizer binding,
RNG continuation, model CLI and architecture boundaries. Ruff, format and
strict mypy cover the new helper. The complete existing CI workflow remains the authoritative
full-suite route; its count, coverage and URL are recorded only after the same-SHA run completes.

## Development audit

The first log-redirection attempt had no output directory, so no test ran and that command was not red
evidence. The real red test then failed because no mismatch was raised. Missing local lint/type tools
were installed only under task scratch; early missing-tool messages were not counted as checks passed.
A partial patch mismatch and a malformed temporary script patch changed no files and were corrected.
Before release, long names in the new test were shortened without weakening assertions, global RNG
cleanup was added, and null/malformed metadata was separated from missing-field compatibility. Strict
mypy caught an imprecise ratio type guard; the final explicit numeric/range check passes without ignores.


## Completed local evidence

Final focused run: 64 tests in 15.663s, OK, exit 0. Nine new methods cover 22 malformed states,
content and ratio mismatch, character-length equality, path relocation, legacy behavior, newline
decoding and prepared/directory input routes. An independent five-process comparison passed all
nine checks: existing checkpoint fields equal (only data_binding added), four output files byte-equal,
and both invalid resume requests leave the run unchanged. Walkthrough length: 3318 Chinese characters.
Machine receipt: `f/1319/解释/data-binding.json`. Same-SHA full CI remains the publication gate.
