# v1321 Per-corpus checkpoint comparison

## User outcome / Step-0

Show which named evaluation corpora improve or regress even when the declared weighted total looks
better. Reuse v1320's paired NLL engine and fixed checkpoints; do not retrain or add a report-only gate.
Baseline main/origin/tag v1320.0.0: `bc9000fb9fedef81dfbff7c563004dbec652bfbf`; CI 34680034239 passed.
Tracked tree is clean; 14 unrelated personal files and ignored interview notes remain untouched.
CodeGraph plus live source inspection found archived run-summary/scorecard aggregation but no grouped
same-window corpus mode in evaluate.py. No old scientific experiment, verdict or fixture is changed.

## Family design (before implementation)

- evaluation.corpora: named input manifest, explicit weight policy, grouped summaries and Markdown.
- evaluate.py: extract the existing one-corpus scoring function; reuse it for plain and grouped calls.
- Existing WindowPlan/score_windows/pair_results remain the actual numerical engine, unchanged.
- Data: version-1 manifest with unique names and paths resolved relative to the manifest; positive weights.
- Behavior: load models once, score each corpus separately, never concatenate/cross corpus boundaries.
- Result: per-group pair results, equal-group macro and declared-weighted NLL; list every regressed group.
- Compatibility: --corpora is opt-in and requires a model pair; v1320 plain/pair output remains equivalent.

## Acceptance matrix

| Requirement | Implementation | Evidence | State |
| --- | --- | --- | --- |
| Mixed-score regression is visible | per-group delta and regression list | weighted improvement with reverse-pattern regression | passed locally |
| Explicit aggregation meaning | equal-corpus macro + declared weight | independently computed weighted NLL; perplexity after aggregation | passed locally |
| Same inputs in each pair | existing fixed_windows_v1 engine | grouped vs individual evaluation equality, no cross-boundary windows | passed locally |
| Efficient repeated evaluation | two model loads per request | actual loader calls do not scale with corpus count | passed locally |
| Stable group sampling | same seed per independent plan | manifest reordering leaves each group's samples/results unchanged | passed locally |
| Fail completely on missing/invalid corpus | no partial publication | short/missing corpus or invalid manifest does not change output | passed locally |
| Existing interface preserved | extracted common function | unchanged v1320 demo and existing tests | passed locally |
| Release and cleanup | original full CI/floors | same-SHA CI success before tag; explicit staging, local notes private | before tag |

## Manifest / CLI contract

`--corpora path/to/corpora.json` selects `{ "version": 1, "corpora": [{"name":"domain", "path":"text.txt", "weight":1}] }`.
Each file is one independently scored corpus, using the same requested split/context/windows/seed.
Paths are relative to the manifest, not current working directory. Missing weight means 1; names/paths
must be unique. Weights are a declared mixture policy, not inferred real-world traffic or confidence.
Use --split all for already-held-out files; default train/val splitting remains explicit in each group.

New mode writes one JSON and adjacent Markdown only after ALL corpora score successfully. It keeps
all per-window results for audit, while the summary shows both aggregate policies and every group.
Existing --data/default invocation keeps v1320 behavior. Grouped mode does not certify holdout provenance.
--data and --corpora are mutually exclusive rather than silently preferring one. An unavailable/too-small
group prevents publication; a failure during final file I/O is not a transaction across JSON/Markdown.

## Failure conditions / non-goals

No weakened test/fixture, hidden failed group, averaged perplexities, silent size-based weighting,
reinitialized models per group, corpus concatenation or changed historical results. Do not report
the aggregate as a global model ranking or automatically promote a checkpoint. Windows overlap and
are correlated. Distinct tokenizer semantics still cannot be compared with raw token perplexity.
Only task-generated synthetic text is archived in the demo; private inputs may appear in report snippets.
Local focused and every fast gate run before push; full suite uses the unchanged same-SHA CI coverage
floor 88.98. Write the walkthrough before final verification. No subagents; one version only.

Strongest objection: weights can manufacture an attractive total. Therefore display the weight policy,
equal-corpus macro result, per-group counts and the regression list beside the weighted result; never
silently suppress a group or treat configured weights as empirical evidence.

## Replayable result and local validation

Run the command in `f/1321/解释/说明.md` using the immutable v1320 demo checkpoints. No model is copied,
retrained or changed this version. The new synthetic manifest assigns forward:reverse weights 9:1:
weighted NLL improves from 1.824759 to 0.831432, while reverse worsens from 1.810937 to 8.202998.
Equal-corpus macro NLL worsens from 1.818616 to 4.107684. These are simultaneous policy-dependent
views of the same per-corpus results, not conflicting measurements or a universal model ranking.

The unchanged new-feature red assertion fails on v1320 because the CLI lacks --corpora. After the
implementation, 48 focused tests pass (4.693s), including 8 new test methods. An independent four-process
comparison shows byte-identical v1320 single-model JSON, paired JSON and paired Markdown. Grouped
reports match individual-corpus evaluations, manifest reordering preserves each report, and only two
checkpoint loads occur. Numerical oracles check NLL weighting (not PPL averaging) and large-weight scaling.
New corpus module passes strict mypy; no old tests, fixtures, model training or fixed_windows_v1 code changed.

## Deliberate boundaries

No new training/quality claim, corpus auto-classification, automatically learned traffic weights or
statistical confidence. A group may have fewer windows when unique starts run out; its declared weight
still applies. Raw corpus paths/snippets occur in diagnostic output. The example is synthetic and safe
to publish; arbitrary user evaluations remain private unless explicitly authorized for publication.
Transient patch-context mismatches during development made no changes; final verification uses the
actual working tree. Full same-SHA CI must succeed before publishing the release tag.
