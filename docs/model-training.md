# Model Training And Evaluation

The model training path is still the educational core of MiniGPT. It includes data preparation, tokenizer experiments, tiny GPT training, evaluation, generation checks, benchmark scorecards, holdout comparisons, and model capability diagnostics.

Important terms:

- `training` means producing or replaying a tiny model run with explicit configuration and artifacts.
- `evaluation` means reading model outputs, holdout rows, benchmark scorecards, or capability diagnostics without overstating production quality.
- `holdout` evidence is useful for comparison, but it is not enough by itself to claim a production-ready model.

Late-stage governance should not hide the model layer. After several publication receipt versions, the project should periodically return to model capability validation such as required-term coverage, loss signal bridge checks, decoder anchor distribution, unassisted repair, or exact surface repair.

See [Model capability cadence](model-capability-cadence.md) for the maintenance rule that keeps governance and readability work from replacing real model checks.

## Compare checkpoints on the same data windows

Use the existing evaluation entrypoint with `--compare-with`:

```powershell
python -B scripts/evaluate.py --checkpoint runs/baseline/checkpoint.pt --compare-with runs/candidate/checkpoint.pt --data data/heldout.txt --split all --windows 128 --batch-size 16 --device cpu --out runs/comparison.json
```

The candidate must use the same tokenizer semantics (a separate file can be supplied with
`--candidate-tokenizer`). By default, both models use the smaller supported context; set
`--context-size` to fix it across multiple comparisons. A private RNG chooses one unique-offset plan,
independent of model initialization. With explicit `--windows`, `--batch-size` only groups execution.
The JSON contains all paired window losses, offsets, source/checkpoint hashes and sampling settings;
the adjacent Markdown shows aggregate NLL/perplexity and the top five improvements/regressions.
Negative candidate-minus-baseline NLL is better on these windows; it is not a global model ranking.

The new `fixed_windows_v1` protocol samples without replacement, caps at available starts, and never
substitutes training data for a short validation slice. With no `--windows`, requested count remains
`eval-iters * batch-size`. Existing single-checkpoint report keys remain, but its numerical evaluation
protocol has changed: do not compare new losses directly with old random-batch reports. train.py's
training-time metrics and archived experimental protocols are unchanged. `--split all` treats the
supplied file as evaluation data; it does not establish whether that file was held out from training.
For train/val, the requested ratio must agree with the experiment's intended split; it is not inferred.

See the [replayable demo and interpretation](../f/1320/解释/说明.md) and
[complete comparison protocol](v1320-paired-evaluation.md). Overlapping windows are correlated,
unknown tokens are counted, and this version does not compute statistical significance or certify
generation quality. Diagnostic reports include short corpus snippets; keep private evaluation data private.

## Step-boundary resume reproducibility

Since v1313, `scripts/train.py` saves an optional version-1 `rng_state` alongside the
model and optimizer. It restores Python, NumPy and Torch CPU generators after setup;
already initialized CUDA generators are captured/restored without starting CUDA on CPU-only runs.
The continuation snapshot excludes terminal sampling and a final-only evaluation that an
uninterrupted run would not perform at that step. Regular evaluation RNG consumption is unchanged.

```powershell
python -B scripts/train.py --data data/sample_zh.txt --out-dir runs/example --max-iters 100 --device cpu
python -B scripts/train.py --data data/sample_zh.txt --resume runs/example/checkpoint.pt --max-iters 200 --device cpu
```

Keep data, tokenizer, batch size, evaluation interval/iterations, hyperparameters and deterministic
runtime identical for an exact trajectory comparison. Epoch or data-loader state is not claimed:
this entrypoint samples batches from the token tensor using Torch RNG. Old checkpoints without
`rng_state` still load but cannot reproduce random state that was never saved. Cross-device or
cross-PyTorch-version bitwise equality is not guaranteed; extra final evaluation rows mean history
files from interrupted and uninterrupted runs need not be identical.

Tests: `python -B -m unittest tests.test_rng_state tests.test_resume_rng -v`.

## Checkpoint publication failures

Since v1314, train.py serializes the existing checkpoint dictionary into a unique temporary file
beside checkpoint.pt. It flushes and fsyncs the open file, closes it, then uses os.replace to publish.
A pre-publication exception leaves the previous checkpoint intact (or no checkpoint on the first save),
and normal Python unwinding removes only that invocation's temporary file. The original error propagates.
The parent directory must exist; train.py creates it during setup as before.

This is single-file isolation, not a transaction over tokenizer.json, metrics, samples or manifests.
Other outputs may already have advanced when saving fails. Abrupt process death before replacement can
leave `.checkpoint.pt.*.tmp`; the controlled kill test verifies the previous checkpoint still loads,
not automatic orphan cleanup. There is no writer lock or directory-entry power-loss durability guarantee.
Checkpoint payloads remain loadable with the existing torch.load path; archive bytes need not be identical
to direct path-based torch.save. See [v1314 evidence and boundaries](v1314-checkpoint-write.md).

Tests: `python -B -m unittest tests.test_checkpoint_io tests.test_resume_rng -v`.

## Tokenizer identity on resume

Since v1315, newly written checkpoints include `tokenizer_sha256`, a SHA-256 digest of a
versioned canonical semantic payload: tokenizer type, ordered `itos`, unknown token and (for BPE)
ordered merge rules. Resume validates this after loading `tokenizer.json` and before constructing
the model or creating the output directory. Formatting/key-order changes do not matter, while a
same-size vocabulary permutation or BPE merge-order change fails closed. Checkpoints without the
field remain loadable for backward compatibility and have no retrospective identity guarantee.

This is an accidental-pairing guard, not authenticity, source-data, hyperparameter or cross-device
verification. It does not migrate inference tools or rewrite historical checkpoints. See
[v1315 tokenizer binding](v1315-tokenizer-binding.md).

## Same-run history recovery

Since v1316, new checkpoints include `history_state`: version 1, the committed metrics.jsonl byte
size, and its SHA-256 digest. When resuming into the checkpoint's own directory, train.py verifies
that exact byte prefix before output writes. Any extra suffix, including a partial JSON/UTF-8 write,
is excluded from the retried history only after preserving the entire original file as
`metrics-<12-hex-digest>.jsonl`. Recovery prints `history_recovered=<backup>` when it acts.
Backup conflicts, missing/altered committed bytes and publication failures stop the run.

Backups are retained recovery evidence; they are not automatically deleted or used as metrics inputs.
Missing legacy metadata keeps previous behavior. Explicit resume into a different output directory
also keeps previous behavior: it neither repairs nor imports the original directory's history.
This is a single-writer, file-sized-memory operation, not a transaction over all run artifacts or
a directory-entry power-loss durability guarantee. RNG and tokenizer guards remain independent.

Reproduce: `python -B -m unittest tests.test_history_recovery tests.test_checkpoint_io tests.test_resume_rng -v`.
See [v1316 scope and evidence](v1316-history-recovery.md).

## Input preflight before output mutation

Since v1317, train.py validates active options immediately after parsing: positive batch/iteration
counts, finite learning rate and ratio, the supported NumPy seed range, fresh-model/BPE settings,
and enabled sampling options. A zero learning rate and zero new sample tokens remain accepted.
`--no-sample` skips sample validation; resume uses checkpoint-owned model/tokenizer configuration
instead of checking ignored fresh-model/BPE CLI values. Values are rejected, not silently clamped.

After tokenization and the existing split/fallback logic, both split lengths are checked against
the effective block size before model allocation and history recovery/output writes. This mirrors
the current get_batch minimum (`block_size + 2` tokens) without changing its sampling behavior or
the tiny-validation fallback. Bad options fail before seeding/input loading; size validation necessarily
follows input reads and seeding. Runtime OOM, disk failures and later training divergence remain possible.

Reproduce: `python -B -m unittest tests.test_train_preflight -v`.
See [v1317 scope, constraints and verification](v1317-train-preflight.md).

## Validate saved random state before restoration

Since v1318, the resume loader validates a non-None RNG snapshot before constructing the model,
recovering metrics or writing outputs. Validation uses isolated Python/NumPy/Torch CPU generators;
it neither installs the saved state into globals nor draws from them. restore_rng_state also validates
the complete supported payload before changing any global CPU state, so malformed later fields cannot
leave earlier generators partially restored. Valid restoration still occurs at the original post-setup
continuation boundary; capture and checkpoint version remain unchanged.

None/missing snapshots keep the legacy no-op behavior. CUDA fields get sequence/tensor structure checks
and CPU normalization only; no CUDA initialization, device-count/driver validation or GPU replay claim.
This is not rollback for native runtime failures or a transaction under concurrent global RNG changes.
train.main still seeds globals before checkpoint loading; the validator's no-mutation guarantee should
not be mistaken for a promise that the whole rejected CLI invocation leaves global RNG untouched.

Reproduce: `python -B -m unittest tests.test_rng_validation tests.test_rng_state tests.test_resume_rng -v`.
See [v1318 scope and evidence](v1318-rng-validation.md).

## Training data identity on resume

Since v1319, newly written checkpoints include an optional version-1 `data_binding` containing
the SHA-256 of the exact UTF-8 text loaded by the run, its character length and `train_ratio`.
Resume compares this semantic input identity before splitting tokens, recovering history or writing
outputs. A same-vocabulary text edit and a changed split ratio therefore fail closed. The source path
is not hashed: identical content at a different path remains a valid branch when the output directory
is explicitly different.

Checkpoints without `data_binding` remain legacy-loadable. The binding is an accidental-drift guard,
not file authenticity, tokenizer identity, optimizer/config validation or cross-device determinism.
Data-directory preparation and ordering keep their existing contract. See [v1319 evidence](v1319-data-binding.md).

Only a missing field is legacy: explicit null, invalid version/length/ratio or a mismatched digest
is rejected. The digest is over the loader's resulting text, not raw source-file bytes; existing
universal-newline decoding and dataset preparation still apply. For example, CRLF and LF source
files loading to the same text have the same identity. `text_length` counts characters, not tokens.
A different output directory does not bypass data validation: it only allows the existing same-input
branch workflow. Changing corpus or ratio is intentionally no longer accepted as an exact resume of
a newly bound checkpoint; this release adds no fine-tuning override or automatic historical rewrite.
