# v1320 Fair paired checkpoint evaluation

## User outcome and Step-0

Goal: answer whether a checkpoint improves next-token likelihood on the SAME samples, and show
where it improves/regresses. This is not another receipt/type-coverage-only version.
Baseline main/origin/tag v1319.0.0: `c01272847fd127f58924868b58ad32996de4f2dc`, CI 34676548593 success.
Tracked tree clean, 14 personal root files untouched, interview notes local-only. CodeGraph consulted
before targeted source reads. Current evaluate.py seeds before model initialization and samples from
the global Torch generator; a width change changes subsequent evaluation windows at the same seed.

## Family design (before implementation)

- evaluation.windows: immutable window plan, private sampling RNG, per-window teacher-forced NLL.
- evaluation.paired: pair summary and human-readable diagnostics, data not report-template subclasses.
- Existing evaluate.py: load checkpoints, choose common context/split, call the same scoring engine.
- Data: loaded text digest, tokenizer identity, explicit offsets/seed/context/protocol in each report.
- Behavior: same unique start positions for both models; batch size is execution grouping when --windows is given.
- Comparison: candidate-minus-baseline NLL, token-normalized perplexity, top improved/regressed windows.
- Boundaries: identical tokenizer semantics required; input holdout provenance is NOT independently certified.

## Requirements and evidence

| Requirement | Implementation | Failing/evaluable check | State |
| --- | --- | --- | --- |
| Initialization-independent evaluation | private window plan | old estimate_loss sees different batches for widths 8/16 | passed locally |
| Same samples and context for A/B | one shared plan, min supported context | input traces/offsets match for both checkpoints | passed locally |
| Correct metric and sign | unreduced cross-entropy per window | analytical uniform predictor and manual CE oracle; swapped A/B reverses delta | passed locally |
| Actionable regression examples | JSON rows + concise Markdown | known improved/regressed windows have correct rankings and snippets | passed locally |
| Honest comparability | tokenizer match, explicit protocol and split | incompatible tokenizers rejected; validation never aliases training data | passed locally |
| Reproducibility | explicit seed/starts/text digest | same model twice yields zero paired delta; batch grouping tolerance checked | passed locally |
| Real demonstration | actual MiniGPT checkpoints | short controlled toy training/evaluation, not just mocks or report strings | passed locally |
| Preserve project scope | no training/core/science/fixture edits | existing tests, fast gates, same-SHA full CI >=88.98 | before tag |

## CLI and compatibility decisions

Extend evaluate.py with --compare-with, --candidate-tokenizer, --context-size and --windows.
--split all supports an explicit standalone evaluation corpus; train/val use a real text slice with
no fallback to training data. Windows are sampled without replacement, capped at available starts.
Defaults retain old argument names; absent --windows requests eval_iters * batch_size windows.
Old report keys remain, but the new fixed_windows_v1 protocol changes numerical sampling: old/new
report losses must NOT be presented as identical-protocol comparisons. Historical reports/experiments
are not rewritten. The old train.py evaluation and experimental decide functions remain untouched.

## DONE / non-goals

Require a reproduced old sampling failure, metric oracles, real CLI comparisons and unchanged quality
floors. Write documentation before final verification. Publish one version only after same-SHA full CI;
annotated tag records the observed full-run result, avoiding speculative or self-referencing receipts.
New production source is kept below 400 lines and modules below existing size gates. No subagents.

Not a model-training improvement, benchmark leaderboard, significance test, multi-seed generalization
claim or generation-quality metric. Overlapping windows are correlated. Different tokenizers cannot
be compared by raw token perplexity here. Unknown-token count and uncertified holdout status are exposed.
No GPU performance claim or network deployment. Output diagnostics contain snippets of the evaluation
corpus; only synthetic/public task-generated demonstration data is eligible for committed examples.

Strongest review question: does a pretty delta merely reflect different evaluation inputs? Tests must
observe actual forward inputs and compare with an independent numerical oracle, not only report keys.

## Local implementation outcome

The unchanged red assertion failed on v1319's architecture-dependent sampling. The final focused
invocation (`tests.test_eval_pairs`, `tests.test_model_cli_behavior`, `tests.test_eval_suite`,
`tests.test_architecture_boundaries`, `tests.test_script_import_boundaries`) passed 40 tests in 4.036s. Eleven new methods cover actual input
traces, manual/uniform NLL oracles, self-pair/repetition, sign/ranking, grouping tolerance, rejected
incompatible inputs and a forward-only replay of the included trained demo.

The attached controlled demo intentionally exposes a regression: candidate training on repeated abc
improves 28 sampled windows but regresses 36 windows in an abc/cba mixture. Mean NLL rises from
1.82166194 to 4.57382700. This is not heldout evidence: see demo/provenance.json for the repeated
training text and fixed seed. Checkpoints are final replay assets (~20 KB each), not task scratch.
Read `f/1320/解释/说明.md`; replay into runs/ so the immutable reference results are not overwritten.

New helpers pass strict mypy. A first scoped type attempt exposed an untyped Torch decorator plus
the script's existing direct-execution import fallback; scoring now uses a no_grad context without
silencing annotations. Strict helper checks are distinguished from the unchanged project-wide scoped
type gate; this release does not claim all existing scripts are strictly typed.

The first full fast-gate sweep caught an existing foundation import contract: evaluate.py must keep
using the public evaluation.prediction facade. The final implementation reuses its existing
perplexity_from_loss helper in both scalar and paired reports; infinite results use JSON null.
No historical assertion or fixture was changed to pass this gate. The sweep is rerun after the fix.

The synthetic corpus deliberately ends each pattern with a space. A demo-local .gitattributes marks
eval.txt's trailing spaces as meaningful text data (and pins repository line endings), rather than
editing its bytes and regenerating a more convenient expected result. Code whitespace rules and
all pre-existing fixtures remain unchanged.

## Run on your own model pair

```powershell
python -B scripts/evaluate.py --checkpoint runs/baseline/checkpoint.pt --compare-with runs/candidate/checkpoint.pt --data data/heldout.txt --split all --windows 128 --context-size 64 --batch-size 16 --device cpu --out runs/comparison.json
```

Both models must support context 64 and use matching tokenizer semantics. The report records each
checkpoint hash and native context limit, selected split/token offset/ratio, complete window starts,
text/tokenizer hashes and the actual evaluated token-occurrence count. Offsets are zero-based input
starts in the full encoded text; target_end_token is inclusive. Previews are capped at 160 characters,
but losses use every token in each full window. No candidate is automatically promoted.
