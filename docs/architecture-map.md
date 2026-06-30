# MiniGPT Architecture Map

This document is the first normalization map for the project. It does not
move code or rename modules. Its job is to give maintainers a stable way to
classify files before later refactors.

## Current Shape

MiniGPT has two overlapping identities:

- A small GPT learning project: tokenizer, dataset, model, training,
  generation, and evaluation.
- An AI engineering governance project: scorecards, model capability checks,
  release gates, publication receipts, registries, artifact indexes, and
  evidence archives.

Those identities should remain visible, but they should not stay mixed at the
same package level forever.

## Layered View

```text
data/
  -> data preparation
  -> tokenizer
  -> dataset batching
  -> MiniGPT model
  -> training scripts
  -> runs/
  -> evaluation and generation
  -> reports and dashboards
  -> gates, receipts, registries, release bundles
```

The preferred dependency direction is inward to outward:

```text
core model/data code
  -> training workflows
  -> run artifacts
  -> evaluation/report readers
  -> governance decisions
  -> release or registry artifacts
```

Outer layers may consume inner-layer artifacts. Inner layers should not depend
on release, registry, receipt, or version-specific governance modules.

## Module Classes

Use these classes before adding or moving files.

| Class | Purpose | Typical files |
|---|---|---|
| `core` | Stable learning-model primitives | `model.py`, `tokenizer.py`, `dataset.py`, `rope.py`, `history.py` |
| `training` | Produces checkpoints or run evidence | `scripts/train.py`, `lm_training.py`, `training_*` |
| `evaluation` | Reads checkpoints or outputs and measures behavior | `eval_suite.py`, `heldout_eval.py`, `benchmark_*`, `generation_quality.py` |
| `serving` | Provides local generation or HTTP-facing wrappers | `server.py`, `server_generator.py`, `server_routes.py` |
| `reports` | Renders JSON, HTML, SVG, Markdown, or dashboards | `dashboard.py`, `*_artifacts.py`, `*_card.py`, `model_report.py` |
| `governance` | Makes pass/fail, promotion, release, receipt, registry, or contract decisions | `release_*`, `registry_*`, `model_capability_*`, `randomized_holdout_*` |
| `research` | Isolated experiments that extend model behavior or analysis | `lora_*`, `sft_*`, `dpo_*`, `distill_*`, `grok_*`, `induction_*` |
| `legacy` | Historical version modules kept for evidence continuity | long versioned receipt/index/check modules no longer used by active flows |

The same file can touch multiple concerns, but it should have one owner class.
If it cannot be assigned one owner, that is a refactor signal.

## First Inventory Snapshot

Approximate source-module counts from the current tree:

| Class | Approximate count | Notes |
|---|---:|---|
| `governance` and capability checks | 1000+ | Dominated by `model_capability_*`, `randomized_holdout_*`, and related chains. |
| `reports` and stable governance summaries | 40+ | Many files repeat writer and renderer patterns. |
| `research` experiments | 30+ | Mostly versioned model-behavior explorations. |
| `evaluation` | 20+ | Benchmark, comparison, eval-suite, and generation-quality code. |
| `core` | 10+ | The small GPT learning path is much smaller than the repository around it. |
| `serving` | 9 | Local generation and HTTP/API wrapper code. |

The exact numbers are less important than the direction: most files now live in
outer governance layers, while the core MiniGPT model remains small.

## Active Flow Map

```text
data_prep.py
  -> tokenizer.py
  -> dataset.py
  -> model.py
  -> scripts/train.py
  -> runs/<run>/
       checkpoint.pt
       tokenizer.json
       metrics.jsonl
       run_manifest.json
  -> scripts/eval_suite.py
  -> eval_suite.py
  -> benchmark/report/gate modules
```

Serving follows a related path:

```text
runs/<run>/checkpoint.pt + tokenizer.json
  -> server_generator.py
  -> server_contracts.py
  -> server_routes.py / server_post_routes.py
  -> server.py / server_http.py
```

Governance follows a read-only evidence path:

```text
run artifacts, scorecards, holdout reports, receipt packets
  -> check/review/index modules
  -> release gates or no-promotion decisions
  -> registry or publication receipt artifacts
```

## Normalization Rules

1. New model primitives should go under the `core` owner class, not into
   governance modules.
2. New report writers should reuse shared report utilities when possible; do
   not add another one-off renderer unless the output contract is genuinely new.
3. New governance modules should have short names. Put long route identity in
   data fields such as `decision`, `route_id`, `source_path`, or `schema_version`
   instead of encoding the whole chain in the filename.
4. Historical files should be frozen unless they are still on an active path or
   must be fixed for tests.
5. Refactors should preserve public behavior first, then move files in small
   batches with focused tests.

`tests/test_architecture_boundaries.py` guards the first narrow set of import
rules: core flat modules and the transitional owner packages must not import
outer release, registry, maturity, route-specific governance, serving, or report
layers. This is not a claim that every historical file has been fully
classified; it is a regression guard for the layers already being normalized.
The same test file also keeps each transitional package module under a small
line budget, so compatibility facades cannot quietly turn into new
hard-to-maintain implementation files.

## Next Refactor Candidates

The safest next steps are:

1. Keep the maintained [module inventory](module-inventory.md) current.
2. Use the [Public API policy](public-api.md) before splitting
   `src/minigpt/__init__.py` into a small stable public API plus explicit
   compatibility exports.
3. Extract common artifact writer helpers used by repeated `_artifacts.py`
   modules.
4. Continue using the transitional owner packages already introduced for
   `core`, `training`, `evaluation`, `serving`, `reports`, and `governance`;
   leave historical chains in place until their consumers are clear.
