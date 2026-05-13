# MiniGPT From Scratch

A PyTorch practice project for building and inspecting a tiny GPT language model.

## Current version

Version 52 is a MiniGPT learning project with registry-level benchmark rubric tracking, rubric-style benchmark correctness scoring, benchmark scorecard drilldowns, benchmark scorecards, project maturity summaries, registry pair delta leaders, registry-level pair batch/trend links, pair batch dashboard/playground links, pair batch trend comparison reports, fixed prompt pair-generation batch reports, persisted side-by-side generation artifacts, side-by-side checkpoint generation, playground checkpoint comparison shortcuts, checkpoint selector support, local inference safety profiles and model-info endpoints, baseline model comparison reports and browser views, dataset version manifests and browser reports, benchmark prompt suite metadata and HTML reports, configurable release gate delta baseline profiles, release gate profile delta explanations, release gate profile comparison reports, release gate policy profiles, release gate generation-quality policy, generation quality evidence-chain integration, generation quality reports, release gates, release evidence bundles, project audit reports, generated model cards, generated experiment cards, registry loss leaderboards and run rankings, run notes and tags in the registry, shareable and exportable registry HTML views, an interactive run registry HTML report, registry indexing for experiments, a benchmark prompt evaluation suite, dataset quality checks and fingerprints, run manifests for experiment reproducibility, dataset preparation and reporting, a local playground server, a static playground Web UI, a sampling lab, multi-run comparison, a static experiment dashboard, model architecture reports, a tiny chat wrapper, next-token prediction inspection, evaluation reports, attention inspection, resumable training, character/BPE tokenizers, source code, tests, code explanations, and archived verification screenshots:

- Python project layout with `src`, `scripts`, `tests`, `data`, `.github/workflows`, `代码讲解记录`, historical `a/<version>` archives, and future `b/<version>` archives
- Character-level tokenizer for turning Chinese text into token ids
- Optional character-seeded BPE tokenizer for understanding subword merge rules
- Tokenizer inspection script for comparing char and BPE tokenization
- Dataset preparation script for merging multiple `.txt` files and exporting dataset reports
- Dataset version manifest with `dataset_name`, `dataset_version`, dataset id, fingerprint, source roots, outputs, quality summary, JSON output, and browser HTML report under `datasets/<name>/<version>` when requested
- Dataset quality report with corpus fingerprint, duplicate-source checks, tiny/empty source warnings, repeated-line hints, JSON output, and SVG summary
- Run manifest writer that records Git metadata, environment, data source, model config, metrics, and artifact inventory for each training run
- Benchmark prompt evaluation suite for running the same Chinese task set against different checkpoints, with suite metadata, task types, difficulty, expected behavior, JSON/CSV/SVG/HTML reports, and dashboard/playground artifact links
- Generation quality analyzer that reads `eval_suite.json` or `sample_lab.json`, checks length/diversity/repetition/prompt echo, and writes `generation_quality.json`, `generation_quality.csv`, `generation_quality.md`, `generation_quality.svg`, and `generation_quality.html`
- Generation quality evidence-chain integration across run registry, model card, and project audit, so generation quality status can affect release-style review
- Run registry builder that indexes multiple run directories, manifests, data fingerprints, quality status, eval suite summaries, metrics, and artifacts
- Run registry HTML report for browsing many experiments, opening dashboard/manifest/eval links, and scanning quality/fingerprint status in a browser
- Registry HTML controls for search, quality filtering, sorting, direction toggling, and visible-row counts
- Registry HTML view state in the URL plus visible-row CSV export for sharing and downstream analysis
- Registry-level pair batch/trend summaries, CSV fields, sortable Pair Reports column, and direct links to each run's pair batch and pair trend HTML reports
- Registry pair delta leaderboard that aggregates pair batch case deltas across many runs, records `pair_delta_summary`, and shows the largest generated deltas in registry HTML
- Project maturity summary builder that reads version tags, archives, code explanations, optional registry evidence, and writes a capability matrix to JSON/CSV/Markdown/HTML
- Benchmark scorecard builder that consolidates eval suite coverage, generation quality, pair consistency, pair delta stability, evidence completeness, and optional registry context into JSON/CSV/Markdown/HTML
- Benchmark scorecard drilldowns that group case scores by task type and difficulty, export a drilldown CSV, and identify the weakest task/difficulty groups
- Rubric-style per-prompt correctness scoring for benchmark scorecards, with explicit `must_include`/`must_avoid` terms, length checks, task-shape checks, weakest-case summaries, and a rubric CSV export
- Registry-level benchmark rubric tracking that reads each run's scorecard, ranks rubric averages, records rubric regressions, and shows Rubric columns/leaderboards in CSV and HTML
- Optional `run_notes.json` annotations with note text, tags, tag counts, CSV columns, SVG summary text, and searchable HTML chips
- Registry best-val leaderboard with per-run rank, loss delta from the current best run, CSV columns, SVG labels, and an HTML leaderboard section
- Experiment card exporter that summarizes one run into `experiment_card.json`, `experiment_card.md`, and `experiment_card.html`, with registry rank, notes, data quality, training, evaluation, artifact, and recommendation sections
- Model card exporter that summarizes a registry and experiment cards into `model_card.json`, `model_card.md`, and `model_card.html`, with intended use, limitations, top runs, coverage, and recommendations
- Project audit exporter that checks registry/model-card readiness and writes `project_audit.json`, `project_audit.md`, and `project_audit.html` with pass/warn/fail checks, score, and recommendations
- Release bundle exporter that combines registry, model card, and project audit evidence into `release_bundle.json`, `release_bundle.md`, and `release_bundle.html`
- Release gate checker that reads `release_bundle.json`, applies a strict pass/warn/fail policy, writes `gate_report.json`, `gate_report.md`, and `gate_report.html`, and exits non-zero when the release is blocked
- Release gate policy profiles (`standard`, `review`, `strict`, and `legacy`) for choosing audit-score thresholds and generation-quality requirements without hand-tuning every CLI flag
- Release gate profile comparison exporter that checks one or more release bundles across selected policy profiles and writes JSON/CSV/Markdown/HTML matrix reports
- Release gate profile delta explanations that compare each profile against the baseline profile and name added/removed failed or warned checks
- Configurable release gate delta baseline profile via `--baseline-profile`, so profile differences can be explained from `standard`, `review`, `strict`, or `legacy` as the reference point
- Release gate generation-quality policy that requires project audit checks `generation_quality` and `non_pass_generation_quality` to be present and clean by default
- Dataset helpers for train/validation split and next-token batch sampling
- Transformer decoder with causal self-attention, multi-head attention, MLP blocks, residual connections, LayerNorm, and tied token embedding/output weights
- Optional attention capture for inspecting causal self-attention maps
- Attention inspection script that exports JSON and SVG heatmaps for a prompt
- Next-token prediction inspection script that exports probability JSON and SVG bar charts
- Evaluation script that reports validation loss and perplexity for a checkpoint
- Model report script that exports parameter groups, per-block parameter counts, tensor shapes, JSON reports, and SVG architecture diagrams
- Dashboard builder that combines run artifacts, eval suites, dataset reports, dataset quality reports, and run manifests into a local `dashboard.html` report
- Playground builder that creates a local `playground.html` UI for prompt controls, command generation, sampling tables, eval suites, run manifests, dataset quality reports, and artifact links
- Playground server that serves the UI and exposes `/api/health`, `/api/checkpoints`, `/api/checkpoint-compare`, `/api/model-info`, `/api/generate`, `/api/generate-pair`, and `/api/generate-pair-artifact` for local live generation
- Local inference safety profile for prompt length, generated token count, temperature, top-k, request body size, and JSONL request logging
- Checkpoint selector API with `/api/checkpoints`, `checkpoint` request selection for `/api/generate`, checkpoint-aware `/api/model-info`, and a playground dropdown for live generation
- Checkpoint comparison API with `/api/checkpoint-compare`, file-size/model/dataset deltas, model-info shortcuts, and a playground table for choosing candidate checkpoints
- Side-by-side checkpoint generation API with `/api/generate-pair`, left/right checkpoint routing, pair comparison summary, JSONL request logging, and a playground two-column output view
- Persisted pair generation artifacts through `/api/generate-pair-artifact`, writing local `pair_generations/*.json` and `pair_generations/*.html` reports with replayable request/output/comparison evidence
- Fixed prompt pair-generation batch script for running a prompt suite across two checkpoints and exporting `pair_generation_batch.json`, `pair_generation_batch.csv`, `pair_generation_batch.md`, and `pair_generation_batch.html`
- Pair batch trend comparison script for comparing saved pair batch reports and exporting `pair_batch_trend.json`, `pair_batch_trend.csv`, `pair_batch_trend.md`, and `pair_batch_trend.html`
- Dashboard and playground artifact links for pair batch and pair trend reports, including a dashboard Pair Batch Reports panel with batch/trend summaries and browser links
- Run comparison script that compares multiple experiments and exports JSON/CSV/SVG/Markdown/HTML summaries
- Baseline model comparison layer with explicit baseline selection, best-val/eval/perplexity/parameter deltas, model signatures, dataset version checks, and recommendations
- Run registry script that discovers or accepts run directories and exports registry JSON/CSV/SVG/HTML summaries
- Sampling lab script that compares generation under multiple `temperature`, `top_k`, and `seed` settings
- Chat prompt utilities for formatting system/user/assistant turns, trimming context windows, and stopping at role markers
- Chat script for one-shot or interactive assistant-style generation from a checkpoint, with transcript JSON output
- Training script with configurable model size, batch size, context window, learning rate, evaluation interval, and CPU/CUDA device selection
- Training script can read a single file, a prepared corpus, or a directory of `.txt` files
- Resumable training with `--resume`, optimizer-state checkpointing, and target-step continuation
- Training artifact output: `metrics.jsonl`, `history_summary.json`, `loss_curve.svg`, `run_manifest.json`, `run_manifest.svg`, and `sample.txt`
- Generation script with checkpoint loading, prompt encoding, temperature sampling, and top-k sampling
- Generation script can write output to a file with `--out`
- History plotting script for rebuilding the loss curve from `metrics.jsonl`
- Sample Chinese training corpus for first-run experiments
- Unit tests for tokenizer, dataset preparation, dataset versioning, dataset quality, benchmark eval suites, registry-level benchmark rubric tracking, rubric-style benchmark scoring, benchmark scorecard drilldowns, benchmark scorecards, project maturity summaries, registry pair delta leaders, registry-level pair report links, pair batch dashboard/playground links, pair batch trend reports, pair batch comparison reports, baseline model comparison reports, inference safety profiles, checkpoint selector, checkpoint comparison, side-by-side generation, and pair artifact APIs, model-info endpoints, request logs, generation quality reports, generation quality evidence-chain integration, run registry, run manifest generation, dataset sampling, history artifacts, model forward/loss, generation shape, prediction inspection, chat prompt handling, model reports, dashboard export, run comparison, sampling lab, playground UI export, playground server API, release bundles, release gates, release gate generation-quality policy, release gate policy profiles, release gate profile comparison reports, release gate profile delta explanations, and configurable delta baselines
- Code explanation records for tokenizer/dataset, model core, train/generate scripts, tests/docs, training artifacts, BPE, attention, prediction/evaluation, chat wrapper, model reports, dashboard export, run comparison, baseline model comparison, sampling lab, playground UI, playground server, inference safety profiles, checkpoint selector, checkpoint comparison shortcuts, side-by-side generation, persisted pair artifacts, fixed prompt pair batch comparison, pair batch trend comparison, pair batch dashboard links, registry pair report links, registry pair delta leaders, project maturity summaries, benchmark scorecards, benchmark scorecard drilldowns, rubric-style benchmark scoring, registry-level benchmark rubric tracking, dataset preparation, dataset versioning, run manifests, dataset quality, eval suites, benchmark prompt suites, generation quality reports, generation quality evidence-chain integration, run registry, registry HTML reporting, registry interaction controls, shareable registry views, registry annotations, registry leaderboards, experiment cards, model cards, project audits, release bundles, release gates, release gate generation-quality policy, release gate policy profiles, release gate profile comparison reports, release gate profile delta explanations, and configurable delta baselines
- Versioned verification archives with key screenshots and command explanations
- GitHub Actions workflow for syntax checks and unit tests

## Version tags

Published tags:

```text
v1.0.0  MiniGPT v1 initial learning project
v2.0.0  MiniGPT v2 training artifacts
v3.0.0  MiniGPT v3 BPE tokenizer
v4.0.0  MiniGPT v4 attention inspection
v5.0.0  MiniGPT v5 prediction inspection
v6.0.0  MiniGPT v6 chat wrapper
v7.0.0  MiniGPT v7 model report
v8.0.0  MiniGPT v8 dashboard
v9.0.0  MiniGPT v9 run comparison
v10.0.0 MiniGPT v10 sampling lab
v11.0.0 MiniGPT v11 playground UI
v12.0.0 MiniGPT v12 playground server
v13.0.0 MiniGPT v13 dataset preparation
v14.0.0 MiniGPT v14 run manifest
v15.0.0 MiniGPT v15 dataset quality
v16.0.0 MiniGPT v16 eval suite
v17.0.0 MiniGPT v17 run registry
v18.0.0 MiniGPT v18 registry HTML
v19.0.0 MiniGPT v19 registry interactions
v20.0.0 MiniGPT v20 registry saved views
v21.0.0 MiniGPT v21 registry annotations
v22.0.0 MiniGPT v22 registry leaderboards
v23.0.0 MiniGPT v23 experiment cards
v24.0.0 MiniGPT v24 model cards
v25.0.0 MiniGPT v25 project audit
v26.0.0 MiniGPT v26 release bundle
v27.0.0 MiniGPT v27 release gate
v28.0.0 MiniGPT v28 generation quality
v29.0.0 MiniGPT v29 generation quality evidence chain
v30.0.0 MiniGPT v30 release gate generation quality policy
v31.0.0 MiniGPT v31 release gate policy profiles
v32.0.0 MiniGPT v32 release gate profile comparison
v33.0.0 MiniGPT v33 release gate profile delta explanations
v34.0.0 MiniGPT v34 configurable release gate delta baseline
v35.0.0 MiniGPT v35 benchmark eval suite metadata
v36.0.0 MiniGPT v36 dataset version manifests
v37.0.0 MiniGPT v37 baseline model comparison
v38.0.0 MiniGPT v38 inference safety profile
v39.0.0 MiniGPT v39 checkpoint selector
v40.0.0 MiniGPT v40 checkpoint comparison shortcuts
v41.0.0 MiniGPT v41 side-by-side checkpoint generation
v42.0.0 MiniGPT v42 persisted pair generation artifacts
v43.0.0 MiniGPT v43 fixed prompt pair generation batches
v44.0.0 MiniGPT v44 pair batch trend comparison
v45.0.0 MiniGPT v45 pair batch dashboard links
v46.0.0 MiniGPT v46 registry pair report links
v47.0.0 MiniGPT v47 registry pair delta leaders
v48.0.0 MiniGPT v48 project maturity summary
v49.0.0 MiniGPT v49 benchmark scorecard
v50.0.0 MiniGPT v50 benchmark scorecard drilldowns
v51.0.0 MiniGPT v51 benchmark rubric scoring
v52.0.0 MiniGPT v52 registry benchmark rubric tracking
```

## Project structure

```text
.
├── .github/
│   └── workflows/
│       └── ci.yml
├── a/
│   ├── 1/
│   │   ├── 图片/
│   │   └── 解释/
│   │       └── 说明.md
│   ├── 2/
│   │   ├── 图片/
│   │   └── 解释/
│   │       └── 说明.md
│   ├── 3/
│   │   ├── 图片/
│   │   └── 解释/
│   │       └── 说明.md
│   ├── 4/
│   │   ├── 图片/
│   │   └── 解释/
│   │       └── 说明.md
│   ├── 5/
│   │   ├── 图片/
│   │   └── 解释/
│   │       └── 说明.md
│   ├── 6/
│   │   ├── 图片/
│   │   └── 解释/
│   │       └── 说明.md
│   ├── 7/
│   │   ├── 图片/
│   │   └── 解释/
│   │       └── 说明.md
│   ├── 8/
│   │   ├── 图片/
│   │   └── 解释/
│   │       └── 说明.md
│   ├── 9/
│   │   ├── 图片/
│   │   └── 解释/
│   │       └── 说明.md
│   ├── 10/
│   │   ├── 图片/
│   │   └── 解释/
│   │       └── 说明.md
│   ├── 11/
│   │   ├── 图片/
│   │   └── 解释/
│   │       └── 说明.md
│   ├── 12/
│   │   ├── 图片/
│   │   └── 解释/
│   │       └── 说明.md
│   ├── 13/
│   │   ├── 图片/
│   │   └── 解释/
│   │       └── 说明.md
│   ├── 14/
│   │   ├── 图片/
│   │   └── 解释/
│   │       └── 说明.md
│   ├── 15/
│   │   ├── 图片/
│   │   └── 解释/
│   │       └── 说明.md
│   ├── 16/
│   │   ├── 图片/
│   │   └── 解释/
│   │       └── 说明.md
│   ├── 17/
│   │   ├── 图片/
│   │   └── 解释/
│   │       └── 说明.md
│   ├── 18/
│   │   ├── 图片/
│   │   └── 解释/
│   │       └── 说明.md
│   ├── 19/
│   │   ├── 图片/
│   │   └── 解释/
│   │       └── 说明.md
│   ├── 20/
│   │   ├── 图片/
│   │   └── 解释/
│   │       └── 说明.md
│   ├── 21/
│   │   ├── 图片/
│   │   └── 解释/
│   │       └── 说明.md
│   ├── 22/
│   │   ├── 图片/
│   │   └── 解释/
│   │       └── 说明.md
│   ├── 23/
│   │   ├── 图片/
│   │   └── 解释/
│   │       └── 说明.md
│   ├── 24/
│   │   ├── 图片/
│   │   └── 解释/
│   │       └── 说明.md
│   ├── 25/
│   │   ├── 图片/
│   │   └── 解释/
│   │       └── 说明.md
│   ├── 26/
│   │   ├── 图片/
│   │   └── 解释/
│   │       └── 说明.md
│   ├── 27/
│   │   ├── 图片/
│   │   └── 解释/
│   │       └── 说明.md
│   ├── 28/
│   │   ├── 图片/
│   │   └── 解释/
│   │       └── 说明.md
│   ├── 29/
│   │   ├── 图片/
│   │   └── 解释/
│   │       └── 说明.md
│   ├── 30/
│   │   ├── 图片/
│   │   └── 解释/
│   │       └── 说明.md
│   └── 31/
│       ├── 图片/
│       └── 解释/
│           └── 说明.md
├── b/
│   ├── README.md
│   ├── 32/
│   │   ├── 图片/
│   │   └── 解释/
│   │       └── 说明.md
│   ├── 33/
│   │   ├── 图片/
│   │   └── 解释/
│   │       └── 说明.md
│   ├── 34/
│   │   ├── 图片/
│   │   └── 解释/
│   │       └── 说明.md
│   ├── 35/
│   │   ├── 图片/
│   │   └── 解释/
│   │       └── 说明.md
│   ├── 36/
│   │   ├── 图片/
│   │   └── 解释/
│   │       └── 说明.md
│   ├── 37/
│   │   ├── 图片/
│   │   └── 解释/
│   │       └── 说明.md
│   ├── 38/
│   │   ├── 图片/
│   │   └── 解释/
│   │       └── 说明.md
│   ├── 39/
│   │   ├── 图片/
│   │   └── 解释/
│   │       └── 说明.md
│   ├── 40/
│   │   ├── 图片/
│   │   └── 解释/
│   │       └── 说明.md
│   └── 41/
│       ├── 图片/
│       └── 解释/
│           └── 说明.md
├── data/
│   ├── eval_prompts.json
│   └── sample_zh.txt
├── scripts/
│   ├── analyze_generation_quality.py
│   ├── audit_project.py
│   ├── build_dashboard.py
│   ├── build_experiment_card.py
│   ├── build_release_bundle.py
│   ├── build_model_card.py
│   ├── build_playground.py
│   ├── chat.py
│   ├── check_release_gate.py
│   ├── compare_release_gate_profiles.py
│   ├── compare_runs.py
│   ├── eval_suite.py
│   ├── evaluate.py
│   ├── generate.py
│   ├── inspect_attention.py
│   ├── inspect_model.py
│   ├── inspect_predictions.py
│   ├── inspect_tokenizer.py
│   ├── plot_history.py
│   ├── playwright_chrome_smoke.ps1
│   ├── prepare_dataset.py
│   ├── register_runs.py
│   ├── sample_lab.py
│   ├── serve_playground.py
│   └── train.py
├── src/
│   └── minigpt/
│       ├── __init__.py
│       ├── chat.py
│       ├── comparison.py
│       ├── dashboard.py
│       ├── data_prep.py
│       ├── data_quality.py
│       ├── dataset.py
│       ├── eval_suite.py
│       ├── experiment_card.py
│       ├── generation_quality.py
│       ├── history.py
│       ├── manifest.py
│       ├── model.py
│       ├── model_card.py
│       ├── model_report.py
│       ├── project_audit.py
│       ├── prediction.py
│       ├── registry.py
│       ├── release_bundle.py
│       ├── release_gate_comparison.py
│       ├── release_gate.py
│       ├── playground.py
│       ├── sampling.py
│       ├── server.py
│       └── tokenizer.py
├── tests/
│   ├── test_attention.py
│   ├── test_chat.py
│   ├── test_comparison.py
│   ├── test_dashboard.py
│   ├── test_data_prep.py
│   ├── test_data_quality.py
│   ├── test_dataset.py
│   ├── test_eval_suite.py
│   ├── test_experiment_card.py
│   ├── test_generation_quality.py
│   ├── test_history.py
│   ├── test_manifest.py
│   ├── test_model.py
│   ├── test_model_card.py
│   ├── test_model_report.py
│   ├── test_playground.py
│   ├── test_prediction.py
│   ├── test_project_audit.py
│   ├── test_registry.py
│   ├── test_release_bundle.py
│   ├── test_release_gate_comparison.py
│   ├── test_release_gate.py
│   ├── test_sampling.py
│   ├── test_server.py
│   └── test_tokenizer.py
├── 代码讲解记录/
│   ├── README.md
│   └── 01-...45-*.md
├── 代码讲解记录_发布治理阶段/
│   ├── README.md
│   ├── 46-v31-release-gate-policy-profiles.md
│   ├── 47-v32-release-gate-profile-comparison.md
│   ├── 48-v33-release-gate-profile-deltas.md
│   └── 49-v34-configurable-release-gate-baseline.md
├── 代码讲解记录_评估基准阶段/
│   ├── README.md
│   ├── 50-v35-benchmark-eval-suite.md
│   ├── 51-v36-dataset-versioning.md
│   ├── 52-v37-baseline-model-comparison.md
│   ├── 53-v38-inference-safety-profile.md
│   ├── 54-v39-checkpoint-selector.md
│   ├── 55-v40-checkpoint-comparison-shortcuts.md
│   └── 56-v41-side-by-side-generation.md
├── AGENTS.md
├── pyproject.toml
├── README.md
├── requirements.txt
└── 解释代码格式说明
```

## Install

If PyTorch is already installed, you can run the project directly. Otherwise:

```powershell
pip install -r requirements.txt
```

## Train

Small CPU-friendly smoke training:

```powershell
python scripts/train.py --device cpu --max-iters 300 --n-layer 2 --n-head 2 --n-embd 64 --batch-size 16 --block-size 64
```

The default output directory is:

```text
runs/minigpt/
```

It contains:

```text
checkpoint.pt
tokenizer.json
train_config.json
metrics.jsonl
history_summary.json
loss_curve.svg
run_manifest.json
run_manifest.svg
sample.txt
```

Resume training from a previous checkpoint:

```powershell
python scripts/train.py --device cpu --resume runs/minigpt/checkpoint.pt --max-iters 600
```

Rebuild the loss curve from history:

```powershell
python scripts/plot_history.py --history runs/minigpt/metrics.jsonl
```

Train with the BPE tokenizer:

```powershell
python scripts/train.py --tokenizer bpe --bpe-vocab-size 260 --max-iters 300
```

Inspect tokenizer behavior:

```powershell
python scripts/inspect_tokenizer.py --tokenizer bpe --bpe-vocab-size 260 --text "人工智能"
```

Inspect attention for a trained checkpoint:

```powershell
python scripts/inspect_attention.py --checkpoint runs/minigpt/checkpoint.pt --prompt "人工智能模型" --layer 0 --head 0
```

Inspect next-token predictions:

```powershell
python scripts/inspect_predictions.py --checkpoint runs/minigpt/checkpoint.pt --prompt "人工智能" --top-k 10
```

Evaluate loss and perplexity:

```powershell
python scripts/evaluate.py --checkpoint runs/minigpt/checkpoint.pt --eval-iters 20
```

Run the benchmark prompt evaluation suite:

```powershell
python scripts/eval_suite.py --checkpoint runs/minigpt/checkpoint.pt --suite data/eval_prompts.json
```

The output directory contains `eval_suite.json`, `eval_suite.csv`, `eval_suite.svg`, and `eval_suite.html`. The default suite records `suite_name`, `suite_version`, task type, difficulty, tags, and expected behavior for continuation, QA, summary, structured output, and factual-consistency prompts.

Analyze generation quality from eval suite or sampling output:

```powershell
python scripts/analyze_generation_quality.py --input runs/minigpt/eval_suite/eval_suite.json --out-dir runs/minigpt/generation-quality
```

The output directory contains `generation_quality.json`, `generation_quality.csv`, `generation_quality.md`, `generation_quality.svg`, and `generation_quality.html`. The analyzer checks continuation length, character diversity, repeated character runs, repeated n-gram ratio, and prompt echo hints.

When a run contains `generation-quality/generation_quality.json` or `eval_suite/generation-quality/generation_quality.json`, the registry, model card, and project audit include generation quality status and case counts.

Inspect model structure and parameter counts:

```powershell
python scripts/inspect_model.py --checkpoint runs/minigpt/checkpoint.pt --sequence-length 64
```

Build a static experiment dashboard:

```powershell
python scripts/build_dashboard.py --run-dir runs/minigpt
```

Prepare a dataset from text files:

```powershell
python scripts/prepare_dataset.py data --out-dir runs/dataset
```

Prepare a named dataset version:

```powershell
python scripts/prepare_dataset.py data --dataset-name sample-zh --dataset-version v1 --dataset-description "Sample Chinese MiniGPT corpus"
```

The output directory contains `corpus.txt`, `dataset_report.json`, `dataset_report.svg`, `dataset_quality.json`, `dataset_quality.svg`, `dataset_version.json`, and `dataset_version.html`. With `--dataset-name` and `--dataset-version`, the default output path is `datasets/<name>/<version>`.

Train from a prepared corpus:

```powershell
python scripts/train.py --prepared-data datasets/sample-zh/v1/corpus.txt --out-dir runs/minigpt
```

Build a static playground UI:

```powershell
python scripts/build_playground.py --run-dir runs/minigpt
```

Serve the playground with a local generation API:

```powershell
python scripts/serve_playground.py --run-dir runs/minigpt --device cpu --max-prompt-chars 2000 --max-new-tokens-limit 512 --checkpoint-candidate runs/minigpt-wide/checkpoint.pt
```

The local server exposes `/api/health`, `/api/checkpoints`, `/api/checkpoint-compare`, `/api/model-info`, `/api/generate`, `/api/generate-pair`, and `/api/generate-pair-artifact`. Generation requests are checked against the inference safety profile (`max_prompt_chars`, `max_new_tokens`, temperature range, `max_top_k`, and `max_body_bytes`) and are recorded in `inference_requests.jsonl` by default. The playground dropdown reads `/api/checkpoints`, sends `checkpoint` in `/api/generate`, asks `/api/model-info?checkpoint=<id>` for the selected checkpoint, renders `/api/checkpoint-compare` as a quick comparison table with model-info shortcuts, sends left/right checkpoint ids to `/api/generate-pair` for side-by-side outputs, and uses `Generate & Save Pair` to write `pair_generations/*.json` plus `pair_generations/*.html` evidence through `/api/generate-pair-artifact`.

Run fixed prompt pair-generation batches across two checkpoints:

```powershell
python scripts/pair_batch.py --left-checkpoint runs/minigpt/checkpoint.pt --right-checkpoint runs/minigpt-wide/checkpoint.pt --left-id base --right-id wide --suite data/eval_prompts.json --out-dir runs/pair_batch
```

The pair batch output directory contains `pair_generation_batch.json`, `pair_generation_batch.csv`, `pair_generation_batch.md`, and `pair_generation_batch.html`, with per-prompt left/right continuations, equality flags, character deltas, suite metadata, and checkpoint ids.

Compare saved pair batch reports across versions or checkpoint pairs:

```powershell
python scripts/compare_pair_batches.py runs/pair_batch_v1/pair_generation_batch.json runs/pair_batch_v2/pair_generation_batch.json --name v1 --name v2 --out-dir runs/pair_batch_trend
```

The trend output directory contains `pair_batch_trend.json`, `pair_batch_trend.csv`, `pair_batch_trend.md`, and `pair_batch_trend.html`, with per-report summaries, per-case equality variants, and maximum absolute character deltas.

Compare multiple run directories:

```powershell
python scripts/compare_runs.py runs/tiny runs/wide --name tiny --name wide --baseline tiny --out-dir runs/comparison
```

The output directory contains `comparison.json`, `comparison.csv`, `comparison.svg`, `comparison.md`, and `comparison.html`. `--baseline` can be a run name, run path, or 1-based index; when omitted, the first run is the baseline.

Build a run registry from multiple run directories:

```powershell
python scripts/register_runs.py runs/tiny runs/wide --name tiny --name wide --out-dir runs/registry
```

The output directory contains `registry.json`, `registry.csv`, `registry.svg`, and `registry.html`. Open `registry.html` to browse runs and jump to each run's dashboard, manifest, and eval suite artifacts.

Optionally add notes and tags to a run before registering it:

```json
{
  "note": "Stable baseline for dataset v1.",
  "tags": ["baseline", "keep"]
}
```

Save that as `run_notes.json` inside the run directory. The registry will include the note and tags in JSON/CSV/SVG/HTML outputs.

The registry also ranks runs by `best_val_loss`. `registry.json` includes `loss_leaderboard`, each run gets `best_val_loss_rank`, `best_val_loss_delta`, and `is_best_val_loss`, and the HTML report shows a Loss Leaderboard panel plus rank/delta sorting.

Build a single-run experiment card:

```powershell
python scripts/build_experiment_card.py --run-dir runs/minigpt --registry runs/registry/registry.json
```

The output directory contains `experiment_card.json`, `experiment_card.md`, and `experiment_card.html`. The card summarizes run status, notes/tags, dataset quality, training settings, evaluation, registry rank, artifacts, and follow-up recommendations.

Build a project-level model card from the registry and experiment cards:

```powershell
python scripts/build_model_card.py --registry runs/registry/registry.json --out-dir runs/model-card
```

The output directory contains `model_card.json`, `model_card.md`, and `model_card.html`. The model card summarizes intended use, limitations, best run, top runs, experiment-card coverage, quality/eval coverage, and next-step recommendations.

Audit project readiness from the registry and model card:

```powershell
python scripts/audit_project.py --registry runs/registry/registry.json --model-card runs/model-card/model_card.json --out-dir runs/audit
```

The output directory contains `project_audit.json`, `project_audit.md`, and `project_audit.html`. The audit checks run coverage, experiment cards, dataset quality, eval suites, checkpoints, dashboards, model-card availability, ready runs, and non-pass quality warnings.

Build a release evidence bundle:

```powershell
python scripts/build_release_bundle.py --registry runs/registry/registry.json --model-card runs/model-card/model_card.json --audit runs/audit/project_audit.json --out-dir runs/release-bundle
```

The output directory contains `release_bundle.json`, `release_bundle.md`, and `release_bundle.html`. The bundle summarizes release status, best run, audit score, top runs, evidence artifacts, and recommendations for handoff.

Check whether a release bundle passes the release gate:

```powershell
python scripts/check_release_gate.py --bundle runs/release-bundle/release_bundle.json --out-dir runs/release-gate --policy-profile standard
```

The output directory contains `gate_report.json`, `gate_report.md`, and `gate_report.html`. The command exits with code `1` when the release is blocked, and `--fail-on-warn` can also make warning states fail CI.

The release gate supports named policy profiles:

```text
standard -> audit score >= 90, at least 1 ready run, generation-quality audit checks required
review   -> audit score >= 80, at least 1 ready run, generation-quality audit checks required
strict   -> audit score >= 95, at least 1 ready run, generation-quality audit checks required
legacy   -> audit score >= 80, at least 1 ready run, generation-quality audit checks not required
```

You can still override profile values with `--min-audit-score`, `--min-ready-runs`, or `--allow-missing-generation-quality` when checking a special bundle.

By default the release gate also requires the project audit to include passing `generation_quality` and `non_pass_generation_quality` checks. Use `--allow-missing-generation-quality` only when checking legacy release bundles that predate v29/v30 generation-quality evidence.

Compare release gate policy profiles for one or more release bundles:

```powershell
python scripts/compare_release_gate_profiles.py --bundle runs/release-bundle/release_bundle.json --profiles standard review strict legacy --out-dir runs/release-gate-profiles
```

Use `--baseline-profile review` when the delta explanations should compare every selected profile against `review` instead of the first selected profile:

```powershell
python scripts/compare_release_gate_profiles.py --bundle runs/release-bundle/release_bundle.json --profiles standard review strict legacy --baseline-profile review --out-dir runs/release-gate-profiles
```

The output directory contains `release_gate_profile_comparison.json`, `release_gate_profile_comparison.csv`, `release_gate_profile_deltas.csv`, `release_gate_profile_comparison.md`, and `release_gate_profile_comparison.html`. Use repeated `--bundle` arguments to compare several release bundles under the same profile set. The reports record `baseline_profile`; the delta CSV and the Markdown/HTML Profile Deltas section explain how each compared profile differs from that baseline profile.

Discover run directories under a parent:

```powershell
python scripts/register_runs.py --discover runs --out-dir runs/registry
```

Verify a local HTML page with Playwright using your installed Google Chrome:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/playwright_chrome_smoke.ps1 -UrlOrPath runs/registry/registry.html -Out tmp/registry-html.png
```

Compare sampling settings for one checkpoint:

```powershell
python scripts/sample_lab.py --checkpoint runs/minigpt/checkpoint.pt --prompt token --max-new-tokens 60
```

## Generate

```powershell
python scripts/generate.py --prompt "人工智能" --max-new-tokens 120
```

Write generated text to a file:

```powershell
python scripts/generate.py --prompt "人工智能" --max-new-tokens 120 --out runs/minigpt/generated.txt
```

## Chat

Run one assistant-style turn:

```powershell
python scripts/chat.py --checkpoint runs/minigpt/checkpoint.pt --message "解释 token 是什么" --out runs/minigpt/transcript.json
```

Start a simple interactive loop:

```powershell
python scripts/chat.py --checkpoint runs/minigpt/checkpoint.pt
```

## Test

```powershell
python -B -m unittest discover -s tests -v
```

## Verification archive

The project keeps real command-output screenshots and explanations under versioned archive directories.

`a/` is the historical archive for v1-v31:

```text
a/1/图片
a/1/解释/说明.md
a/2/图片
a/2/解释/说明.md
a/3/图片
a/3/解释/说明.md
a/4/图片
a/4/解释/说明.md
a/5/图片
a/5/解释/说明.md
a/6/图片
a/6/解释/说明.md
a/7/图片
a/7/解释/说明.md
a/8/图片
a/8/解释/说明.md
a/9/图片
a/9/解释/说明.md
a/10/图片
a/10/解释/说明.md
a/11/图片
a/11/解释/说明.md
a/12/图片
a/12/解释/说明.md
a/13/图片
a/13/解释/说明.md
a/14/图片
a/14/解释/说明.md
a/15/图片
a/15/解释/说明.md
a/16/图片
a/16/解释/说明.md
a/17/图片
a/17/解释/说明.md
a/18/图片
a/18/解释/说明.md
a/19/图片
a/19/解释/说明.md
a/20/图片
a/20/解释/说明.md
a/21/图片
a/21/解释/说明.md
a/22/图片
a/22/解释/说明.md
a/23/图片
a/23/解释/说明.md
a/24/图片
a/24/解释/说明.md
a/25/图片
a/25/解释/说明.md
a/26/图片
a/26/解释/说明.md
a/27/图片
a/27/解释/说明.md
a/28/图片
a/28/解释/说明.md
a/29/图片
a/29/解释/说明.md
a/30/图片
a/30/解释/说明.md
a/31/图片
a/31/解释/说明.md
```

Starting with v32, new run screenshots and explanations should be written under `b/`, which is a sibling directory of `a/`:

```text
b/32/图片
b/32/解释/说明.md
b/33/图片
b/33/解释/说明.md
b/34/图片
b/34/解释/说明.md
b/35/图片
b/35/解释/说明.md
b/36/图片
b/36/解释/说明.md
b/37/图片
b/37/解释/说明.md
b/38/图片
b/38/解释/说明.md
b/39/图片
b/39/解释/说明.md
b/40/图片
b/40/解释/说明.md
b/41/图片
b/41/解释/说明.md
b/42/图片
b/42/解释/说明.md
b/43/图片
b/43/解释/说明.md
b/44/图片
b/44/解释/说明.md
b/45/图片
b/45/解释/说明.md
b/46/图片
b/46/解释/说明.md
b/47/图片
b/47/解释/说明.md
b/48/图片
b/48/解释/说明.md
```

Version 1 screenshots:

- `01-project-tree.png`: project structure check
- `02-unit-tests.png`: unit test run
- `03-train-smoke.png`: real training smoke test
- `04-generate-smoke.png`: checkpoint loading and generation smoke test
- `05-code-explanation-check.png`: code explanation document check

Version 2 screenshots:

- `01-unit-tests.png`: expanded unit tests
- `02-train-history-smoke.png`: training writes history, summary, SVG, and sample artifacts
- `03-resume-smoke.png`: resumed training continues from an existing checkpoint
- `04-plot-and-generate-out.png`: standalone history plot and generated output file
- `05-docs-check.png`: v2 docs and archive check

Version 3 screenshots:

- `01-unit-tests.png`: expanded tokenizer and regression tests
- `02-bpe-inspect.png`: BPE tokenizer merge inspection
- `03-bpe-train-smoke.png`: BPE training smoke test
- `04-bpe-generate-load.png`: BPE checkpoint generation and tokenizer reload
- `05-docs-check.png`: v3 docs and archive check

Version 4 screenshots:

- `01-unit-tests.png`: attention capture and regression tests
- `02-attention-train-smoke.png`: checkpoint training smoke for attention inspection
- `03-attention-export.png`: attention JSON/SVG export
- `04-attention-artifacts-check.png`: exported attention artifact check
- `05-docs-check.png`: v4 docs and archive check

Version 5 screenshots:

- `01-unit-tests.png`: prediction/evaluation regression tests
- `02-prediction-train-smoke.png`: checkpoint training smoke for prediction inspection
- `03-inspect-predictions.png`: next-token prediction JSON/SVG export
- `04-evaluate-report.png`: evaluation report with loss and perplexity
- `05-docs-check.png`: v5 docs and archive check

Version 6 screenshots:

- `01-unit-tests.png`: chat prompt and existing regression tests
- `02-chat-train-smoke.png`: checkpoint training smoke for chat wrapper
- `03-chat-one-shot.png`: one-shot chat generation and transcript export
- `04-transcript-check.png`: transcript JSON structure check
- `05-docs-check.png`: v6 docs and archive check

Version 7 screenshots:

- `01-unit-tests.png`: model report and existing regression tests
- `02-model-report-train-smoke.png`: checkpoint training smoke for model report
- `03-inspect-model.png`: model report JSON/SVG export
- `04-model-report-json-check.png`: report JSON structure check
- `05-docs-check.png`: v7 docs and archive check

Version 8 screenshots:

- `01-unit-tests.png`: dashboard and existing regression tests
- `02-dashboard-artifacts-smoke.png`: run artifact preparation for dashboard
- `03-build-dashboard.png`: dashboard HTML export
- `04-dashboard-html-check.png`: generated dashboard structure check
- `05-docs-check.png`: v8 docs and archive check

Version 9 screenshots:

- `01-unit-tests.png`: comparison and existing regression tests
- `02-comparison-runs-smoke.png`: two run directories prepared for comparison
- `03-compare-runs.png`: comparison JSON/CSV/SVG export
- `04-comparison-artifacts-check.png`: comparison artifact structure check
- `05-docs-check.png`: v9 docs and archive check

Version 10 screenshots:

- `01-unit-tests.png`: sampling lab and existing regression tests
- `02-sampling-train-smoke.png`: checkpoint training smoke for sampling lab
- `03-sample-lab.png`: multi-configuration sampling JSON/CSV/SVG export
- `04-sampling-artifacts-check.png`: sampling artifact structure check
- `05-docs-check.png`: v10 docs and archive check

Version 11 screenshots:

- `01-unit-tests.png`: playground UI, dashboard, and comparison regression tests; full torch-backed test discovery was attempted but timed out in this Windows session
- `02-playground-artifacts-smoke.png`: lightweight run artifacts prepared for playground
- `03-build-playground.png`: playground HTML export
- `04-playground-html-check.png`: generated playground structure check
- `05-docs-check.png`: v11 docs and archive check

Version 12 screenshots:

- `01-unit-tests.png`: server API, playground UI, and existing regression tests
- `02-server-train-smoke.png`: small checkpoint prepared for live server generation
- `03-serve-playground.png`: local server health and generation API smoke
- `04-server-artifacts-check.png`: server output and artifact structure check
- `05-docs-check.png`: v12 docs and archive check

Version 13 screenshots:

- `01-unit-tests.png`: dataset preparation and existing regression tests
- `02-prepare-dataset.png`: multi-file corpus preparation and report export
- `03-train-prepared-data.png`: training from prepared corpus
- `04-dataset-artifacts-check.png`: dataset report and dashboard/playground artifact checks
- `05-docs-check.png`: v13 docs and archive check

Version 14 screenshots:

- `01-unit-tests.png`: run manifest and existing regression tests
- `02-train-manifest-smoke.png`: training writes run manifest JSON/SVG
- `03-manifest-json-check.png`: manifest metadata, Git, data, model, training, and artifact checks
- `04-dashboard-playground-manifest.png`: dashboard/playground manifest artifact checks
- `05-docs-check.png`: v14 docs and archive check

Version 15 screenshots:

- `01-unit-tests.png`: dataset quality and existing regression tests
- `02-prepare-quality-smoke.png`: dataset preparation writes quality JSON/SVG
- `03-quality-json-check.png`: fingerprint, status, duplicate, and repeated-line checks
- `04-train-dashboard-quality.png`: training/dashboard/playground carry dataset quality artifacts
- `05-docs-check.png`: v15 docs and archive check

Version 16 screenshots:

- `01-unit-tests.png`: eval suite and existing regression tests
- `02-train-eval-suite-smoke.png`: train a small checkpoint and run fixed prompt eval suite
- `03-eval-suite-json-check.png`: eval suite JSON/CSV/SVG artifact checks
- `04-dashboard-playground-eval-suite.png`: dashboard/playground eval suite artifact checks
- `05-docs-check.png`: v16 docs and archive check

Version 17 screenshots:

- `01-unit-tests.png`: run registry and existing regression tests
- `02-registry-runs-smoke.png`: two run directories prepared with eval suite/dashboard artifacts
- `03-register-runs.png`: registry JSON/CSV/SVG export
- `04-registry-json-check.png`: registry best run, quality counts, fingerprints, and artifact checks
- `05-docs-check.png`: v17 docs and archive check

Version 18 screenshots:

- `01-unit-tests.png`: registry HTML and existing regression tests
- `02-registry-html-smoke.png`: two small runs prepared and registered with HTML output
- `03-registry-html-check.png`: generated registry HTML opened through Playwright with installed Google Chrome
- `04-registry-discover-check.png`: discovery mode exports JSON/CSV/SVG/HTML
- `05-docs-check.png`: v18 docs and archive check

Version 19 screenshots:

- `01-unit-tests.png`: registry interaction tests and existing regression tests
- `02-registry-interactive-smoke.png`: two small runs registered with searchable/sortable HTML output
- `03-playwright-filter-check.png`: Playwright Chrome search, quality filter, sort, and count check
- `04-registry-html-structure-check.png`: HTML controls, row data attributes, and escaping checks
- `05-docs-check.png`: v19 docs and archive check

Version 20 screenshots:

- `01-unit-tests.png`: saved-view/export tests and existing regression tests
- `02-registry-views-smoke.png`: two small runs registered with shareable/exportable registry HTML output
- `03-playwright-view-export-check.png`: Playwright Chrome hash-state restore, Share button, and visible CSV download check
- `04-registry-html-structure-check.png`: URL state, clipboard, CSV export, controls, and escaping checks
- `05-docs-check.png`: v20 docs and archive check

Version 21 screenshots:

- `01-unit-tests.png`: registry annotations tests and existing regression tests
- `02-registry-notes-smoke.png`: two small runs registered with `run_notes.json` annotations
- `03-playwright-notes-search-check.png`: Playwright Chrome tag search and Notes column check
- `04-registry-notes-structure-check.png`: JSON/CSV/SVG/HTML notes, tags, tag counts, and escaping checks
- `05-docs-check.png`: v21 docs and archive check

Version 22 screenshots:

- `01-unit-tests.png`: registry leaderboard tests and existing regression tests
- `02-registry-leaderboard-smoke.png`: three small runs registered with rank and loss delta output
- `03-registry-leaderboard-structure-check.png`: JSON/CSV/SVG/HTML leaderboard, rank, and delta checks
- `04-playwright-leaderboard-screenshot.png`: registry HTML opened through Playwright with installed Google Chrome
- `05-docs-check.png`: v22 docs and archive check

Version 23 screenshots:

- `01-unit-tests.png`: experiment card and integration tests plus existing regression tests
- `02-experiment-card-smoke.png`: two small runs, registry ranking, card generation, dashboard/playground integration, and registry refresh
- `03-experiment-card-structure-check.png`: JSON/Markdown/HTML card fields plus dashboard/playground/registry links
- `04-playwright-experiment-card.png`: experiment card HTML opened through Playwright with installed Google Chrome
- `05-docs-check.png`: v23 docs and archive check

Version 24 screenshots:

- `01-unit-tests.png`: model card tests plus existing regression tests
- `02-model-card-smoke.png`: registry, two experiment cards, and project-level model card generation
- `03-model-card-structure-check.png`: JSON/Markdown/HTML model card coverage, top run, links, and recommendations
- `04-playwright-model-card.png`: model card HTML opened through Playwright with installed Google Chrome
- `05-docs-check.png`: v24 docs and archive check

Version 25 screenshots:

- `01-unit-tests.png`: project audit tests plus existing regression tests
- `02-project-audit-smoke.png`: registry, experiment cards, model card, and project audit generation
- `03-project-audit-structure-check.png`: JSON/Markdown/HTML audit status, checks, runs, and recommendations
- `04-playwright-project-audit.png`: project audit HTML opened through Playwright with installed Google Chrome
- `05-docs-check.png`: v25 docs and archive check

Version 26 screenshots:

- `01-unit-tests.png`: release bundle tests plus existing regression tests
- `02-release-bundle-smoke.png`: registry, experiment cards, model card, project audit, and release bundle generation
- `03-release-bundle-structure-check.png`: JSON/Markdown/HTML release status, top runs, audit checks, and evidence artifacts
- `04-playwright-release-bundle.png`: release bundle HTML opened through Playwright with installed Google Chrome
- `05-docs-check.png`: v26 docs and archive check

Version 27 screenshots:

- `01-unit-tests.png`: release gate tests plus existing regression tests
- `02-release-gate-smoke.png`: release bundle input checked through the release gate CLI
- `03-release-gate-structure-check.png`: JSON/Markdown/HTML gate status, policy, checks, and decision fields
- `04-playwright-release-gate.png`: release gate HTML opened through Playwright with installed Google Chrome
- `05-docs-check.png`: v27 docs and archive check

Version 28 screenshots:

- `01-unit-tests.png`: generation quality tests plus existing regression tests
- `02-generation-quality-smoke.png`: eval suite input analyzed through the generation quality CLI
- `03-generation-quality-structure-check.png`: JSON/Markdown/SVG/HTML quality status, policy, cases, and flags
- `04-playwright-generation-quality.png`: generation quality HTML opened through Playwright with installed Google Chrome
- `05-docs-check.png`: v28 docs and archive check

Version 29 screenshots:

- `01-unit-tests.png`: registry/model-card/audit generation quality integration tests plus existing regression tests
- `02-generation-quality-chain-smoke.png`: two runs carrying generation quality reports through registry, model card, and project audit
- `03-generation-quality-chain-structure-check.png`: JSON/Markdown/HTML checks for generation quality fields across the evidence chain
- `04-playwright-registry-generation-quality.png`: registry HTML with generation quality columns and links opened through Playwright with installed Google Chrome
- `05-docs-check.png`: v29 docs and archive check

Version 30 screenshots:

- `01-unit-tests.png`: release gate generation-quality policy tests plus existing regression tests
- `02-release-gate-generation-quality-smoke.png`: release bundle with generation quality audit checks passing the release gate
- `03-release-gate-generation-quality-structure-check.png`: gate report policy/check fields plus legacy bundle blocking evidence
- `04-playwright-release-gate-generation-quality.png`: release gate HTML opened through Playwright with installed Google Chrome
- `05-docs-check.png`: v30 docs and archive check

Version 31 screenshots:

- `01-unit-tests.png`: release gate policy profile tests plus existing regression tests
- `02-release-gate-policy-profiles-smoke.png`: standard/review/strict/legacy profiles checked against release bundle fixtures
- `03-release-gate-policy-profiles-structure-check.png`: gate report policy profile fields, thresholds, overrides, and CLI output checked
- `04-playwright-release-gate-policy-profiles.png`: release gate HTML opened through Playwright with installed Google Chrome
- `05-docs-check.png`: v31 docs, new code explanation phase directory, and archive check

Version 32 screenshots:

- `01-unit-tests.png`: release gate profile comparison tests plus existing regression tests
- `02-release-gate-profile-comparison-smoke.png`: one or more release bundles compared across standard/review/strict/legacy profiles
- `03-release-gate-profile-comparison-structure-check.png`: JSON/CSV/Markdown/HTML comparison fields and blocked/approved counts checked
- `04-playwright-release-gate-profile-comparison.png`: comparison HTML opened through Playwright with installed Google Chrome
- `05-docs-check.png`: v32 docs, b/32 archive, and release-governance explanation check

Version 33 screenshots:

- `01-unit-tests.png`: release gate profile delta tests plus existing regression tests
- `02-release-gate-profile-deltas-smoke.png`: comparison CLI output with delta counts and delta CSV path
- `03-release-gate-profile-deltas-structure-check.png`: JSON/CSV/Markdown/HTML delta fields, explanations, and added/removed checks verified
- `04-playwright-release-gate-profile-deltas.png`: comparison HTML Profile Deltas section opened through Playwright with installed Google Chrome
- `05-docs-check.png`: v33 docs, b/33 archive, and release-governance explanation check

Version 34 screenshots:

- `01-unit-tests.png`: release gate configurable baseline tests plus existing regression tests
- `02-release-gate-baseline-profile-smoke.png`: comparison CLI output with `baseline_profile=review`
- `03-release-gate-baseline-profile-structure-check.png`: JSON/CSV/Markdown/HTML baseline fields and review-based deltas verified
- `04-playwright-release-gate-baseline-profile.png`: comparison HTML with baseline `review` opened through Playwright with installed Google Chrome
- `05-docs-check.png`: v34 docs, b/34 archive, and release-governance explanation check

Version 35 screenshots:

- `01-unit-tests.png`: benchmark eval suite metadata tests plus existing regression tests
- `02-benchmark-eval-suite-smoke.png`: benchmark suite fixture exported to JSON/CSV/SVG/HTML
- `03-benchmark-eval-suite-structure-check.png`: suite metadata, task counts, CSV fields, dashboard/playground links, and registry artifacts verified
- `04-playwright-benchmark-eval-suite.png`: eval suite HTML report opened through Playwright with installed Google Chrome
- `05-docs-check.png`: v35 docs, b/35 archive, and evaluation-benchmark explanation check

Version 36 screenshots:

- `01-unit-tests.png`: dataset versioning tests plus existing regression tests
- `02-dataset-version-smoke.png`: named dataset version prepared under `datasets/<name>/<version>`
- `03-dataset-version-structure-check.png`: `dataset_version.json/html`, manifest, dashboard, playground, and registry artifact links verified
- `04-playwright-dataset-version.png`: dataset version HTML report opened through Playwright with installed Google Chrome
- `05-docs-check.png`: v36 docs, b/36 archive, and evaluation-benchmark explanation check

Version 37 screenshots:

- `01-unit-tests.png`: baseline model comparison tests plus existing regression tests
- `02-baseline-comparison-smoke.png`: three fixture runs compared with `baseline-char` as the selected baseline
- `03-baseline-comparison-structure-check.png`: JSON/CSV/SVG/Markdown/HTML baseline delta fields verified
- `04-playwright-baseline-comparison.png`: comparison HTML opened through Playwright with installed Google Chrome
- `05-docs-check.png`: v37 docs, b/37 archive, and evaluation-benchmark explanation check

Version 38 screenshots:

- `01-unit-tests.png`: inference safety profile, model-info endpoint, request log tests, and existing regression tests
- `02-server-safety-smoke.png`: local HTTP server smoke for health/model-info/generate/rejected request/logging
- `03-server-safety-structure-check.png`: request log records, safety rejection, and model metadata checks verified
- `04-playwright-model-info.png`: `/api/model-info` opened through Playwright with installed Google Chrome
- `05-docs-check.png`: v38 docs, b/38 archive, and evaluation-benchmark explanation check

Version 39 screenshots:

- `01-unit-tests.png`: checkpoint selector API, playground dropdown, model-info selector, request log tests, and existing regression tests
- `02-checkpoint-selector-smoke.png`: local HTTP smoke for default/wide checkpoint discovery, selected generation, and missing-checkpoint rejection
- `03-checkpoint-selector-structure-check.png`: checkpoint endpoint, model-info selector, request log fields, and playground `payload.checkpoint` wiring verified
- `04-playwright-checkpoint-selector.png`: playground checkpoint selector opened through Playwright with installed Google Chrome
- `05-docs-check.png`: v39 docs, b/39 archive, and evaluation-benchmark explanation check

Version 40 screenshots:

- `01-unit-tests.png`: checkpoint comparison API, playground comparison table, selector integration, and existing regression tests
- `02-checkpoint-compare-smoke.png`: local HTTP smoke for `/api/checkpoint-compare`, metadata deltas, model-info shortcut, selected generation, and bad selector rejection
- `03-checkpoint-compare-structure-check.png`: comparison summary, ready counts, model/dataset deltas, model-info links, and playground action wiring verified
- `04-playwright-checkpoint-compare.png`: playground checkpoint comparison table opened through Playwright with installed Google Chrome
- `05-docs-check.png`: v40 docs, b/40 archive, and evaluation-benchmark explanation check

Version 41 screenshots:

- `01-unit-tests.png`: side-by-side generation API, pair request parsing, pair request logs, playground pair controls, and existing regression tests
- `02-generate-pair-smoke.png`: local HTTP smoke for `/api/generate-pair`, left/right checkpoint routing, comparison summary, selected single generation, and bad pair rejection
- `03-generate-pair-structure-check.png`: pair response fields, pair log fields, prompt controls, left/right selectors, and playground output panels verified
- `04-playwright-generate-pair.png`: playground side-by-side generation view opened through Playwright with installed Google Chrome
- `05-docs-check.png`: v41 docs, b/41 archive, and evaluation-benchmark explanation check

Version 42 screenshots:

- `01-unit-tests.png`: persisted pair artifact API, JSON/HTML writer, artifact logging, playground save controls, and regression tests
- `02-generate-pair-artifact-smoke.png`: local HTTP smoke for `/api/generate-pair-artifact`, JSON/HTML artifact paths, selected pair generation, saved HTML, and bad pair rejection
- `03-generate-pair-artifact-structure-check.png`: artifact record schema, HTML content, artifact hrefs, pair log artifact paths, and playground save controls verified
- `04-playwright-pair-artifacts.png`: playground save-pair controls opened through Playwright with installed Google Chrome
- `05-docs-check.png`: v42 docs, b/42 archive, and evaluation-benchmark explanation check

Version 43 screenshots:

- `01-unit-tests.png`: pair batch report builders, JSON/CSV/Markdown/HTML writers, CLI compile, and regression tests
- `02-pair-batch-cli-smoke.png`: tiny PyTorch checkpoint smoke for `scripts/pair_batch.py`, fixed prompt suite execution, and saved batch outputs
- `03-pair-batch-structure-check.png`: batch report schema, equality/delta summaries, CSV columns, Markdown table, and HTML report content verified
- `04-playwright-pair-batch-html.png`: generated `pair_generation_batch.html` opened through Playwright with installed Google Chrome
- `05-docs-check.png`: v43 docs, b/43 archive, and evaluation-benchmark explanation check

Version 44 screenshots:

- `01-unit-tests.png`: pair trend report builders, trend writers, CLI compile, and regression tests
- `02-pair-trend-cli-smoke.png`: saved pair batch reports compared through `scripts/compare_pair_batches.py` with JSON/CSV/Markdown/HTML outputs
- `03-pair-trend-structure-check.png`: trend schema, report summaries, per-case equality variants, CSV rows, Markdown table, and HTML report content verified
- `04-playwright-pair-trend-html.png`: generated `pair_batch_trend.html` opened through Playwright with installed Google Chrome
- `05-docs-check.png`: v44 docs, b/44 archive, and evaluation-benchmark explanation check

Version 45 screenshots:

- `01-unit-tests.png`: dashboard/playground pair batch links, dashboard Pair Batch Reports panel, link discovery, command helpers, and regression tests
- `02-dashboard-playground-smoke.png`: local run artifacts rendered through dashboard and playground builders with pair batch/trend links
- `03-dashboard-playground-structure-check.png`: dashboard summary fields, pair batch panel links, playground Run Files links, and command helper strings verified
- `04-playwright-dashboard-pair-links.png`: generated dashboard Pair Batch Reports panel opened through Playwright with installed Google Chrome
- `05-docs-check.png`: v45 docs, b/45 archive, and evaluation-benchmark explanation check

Version 46 screenshots:

- `01-unit-tests.png`: registry pair report fields, CSV columns, HTML Pair Reports column, links, sorting metadata, compile check, and regression tests
- `02-registry-pair-smoke.png`: two local runs registered with pair batch/trend summaries, pair report counts, CSV fields, and HTML links
- `03-registry-pair-structure-check.png`: registry JSON fields, Pair Reports column, link hrefs, sort option, and output files verified
- `04-playwright-registry-pair-links.png`: generated registry HTML opened through Playwright with installed Google Chrome and pair report links visible
- `05-docs-check.png`: v46 docs, b/46 archive, and evaluation-benchmark explanation check

Version 47 screenshots:

- `01-unit-tests.png`: registry pair delta summary, leaderboard sorting, Pair Delta Leaders HTML panel, compile check, and regression tests
- `02-registry-pair-delta-smoke.png`: three local runs registered with cross-run pair delta summary and largest generated-delta leaderboard
- `03-registry-pair-delta-structure-check.png`: registry JSON summary, leaderboard rows, relative report links, stats card, and HTML panel verified
- `04-playwright-registry-pair-delta-leaders.png`: generated registry HTML opened through Playwright with installed Google Chrome and Pair Delta Leaders visible
- `05-docs-check.png`: v47 docs, b/47 archive, and evaluation-benchmark explanation check

Version 48 screenshots:

- `01-unit-tests.png`: maturity summary builder, output writers, HTML escaping, compile check, and full regression tests
- `02-maturity-summary-smoke.png`: project maturity summary generated from the repo with capability matrix, phase timeline, and recommendations
- `03-maturity-summary-structure-check.png`: JSON summary, CSV columns, Markdown sections, HTML cards, and project maturity phase docs verified
- `04-playwright-maturity-summary-html.png`: generated maturity summary HTML opened through Playwright with installed Google Chrome
- `05-docs-check.png`: v48 docs, b/48 archive, and project-maturity explanation check

Version 49 screenshots:

- `01-unit-tests.png`: benchmark scorecard builder, output writers, HTML escaping, compile check, and full regression tests
- `02-benchmark-scorecard-smoke.png`: local run scorecard generated with components, case scores, outputs, and registry context
- `03-benchmark-scorecard-structure-check.png`: JSON summary, CSV columns, Markdown sections, HTML cards, and case-score rows verified
- `04-playwright-benchmark-scorecard-html.png`: generated benchmark scorecard HTML opened through Playwright with installed Google Chrome
- `05-docs-check.png`: v49 docs, b/49 archive, and project-maturity explanation check

Version 50 screenshots:

- `01-unit-tests.png`: benchmark scorecard drilldown tests, output writers, HTML escaping, compile check, and full regression tests
- `02-benchmark-scorecard-drilldown-smoke.png`: local run scorecard generated with task-type and difficulty groups plus weakest-group summaries
- `03-benchmark-scorecard-drilldown-structure-check.png`: JSON drilldowns, drilldown CSV columns, Markdown sections, HTML panels, and schema v2 verified
- `04-playwright-benchmark-scorecard-drilldowns.png`: generated scorecard drilldown HTML opened through Playwright with installed Google Chrome
- `05-docs-check.png`: v50 docs, b/50 archive, and project-maturity explanation check

Version 51 screenshots:

- `01-unit-tests.png`: rubric-style benchmark scoring tests, output writers, HTML escaping, compile check, and full regression tests
- `02-benchmark-rubric-smoke.png`: local run scorecard generated with rubric status, average score, weakest case, and rubric CSV output
- `03-benchmark-rubric-structure-check.png`: JSON schema v3, rubric scores, rubric CSV columns, Markdown section, HTML panel, and drilldown rubric fields verified
- `04-playwright-benchmark-rubric-html.png`: generated benchmark rubric HTML opened through Playwright with installed Google Chrome
- `05-docs-check.png`: v51 docs, b/51 archive, and project-maturity explanation check

Version 52 screenshots:

- `01-unit-tests.png`: registry benchmark rubric tests, compile check, and full regression tests
- `02-registry-rubric-smoke.png`: local multi-run registry generated with rubric counts, leaderboard, regression summary, and CLI output
- `03-registry-rubric-structure-check.png`: registry JSON summary, CSV rubric columns, HTML Rubric column, sort option, links, and leaderboard verified
- `04-playwright-registry-rubric-html.png`: generated registry rubric HTML opened through Playwright with installed Google Chrome
- `05-docs-check.png`: v52 docs, b/52 archive, and project-maturity explanation check

## Code explanation records

Start here:

```text
代码讲解记录/README.md
代码讲解记录_发布治理阶段/README.md
代码讲解记录_评估基准阶段/README.md
```

The original `代码讲解记录` directory keeps the v1-v30 history in place. v31-v34 release-governance records live in `代码讲解记录_发布治理阶段`; v35 and later benchmark/evaluation records start in `代码讲解记录_评估基准阶段` so the project can split future phases without moving old evidence.

First-stage reading order:

```text
01-tokenizer-and-dataset.md
02-model-core.md
03-train-generate.md
04-tests-docs.md
05-v2-training-artifacts.md
06-version-2-tests-docs.md
07-v3-bpe-tokenizer.md
08-version-3-tests-docs.md
09-v4-attention-inspection.md
10-version-4-tests-docs.md
11-v5-prediction-evaluation.md
12-version-5-tests-docs.md
13-v6-chat-wrapper.md
14-version-6-tests-docs.md
15-v7-model-report.md
16-version-7-tests-docs.md
17-v8-dashboard.md
18-version-8-tests-docs.md
19-v9-run-comparison.md
20-version-9-tests-docs.md
21-v10-sampling-lab.md
22-version-10-tests-docs.md
23-v11-playground-ui.md
24-version-11-tests-docs.md
25-v12-playground-server.md
26-version-12-tests-docs.md
27-v13-dataset-preparation.md
28-version-13-tests-docs.md
29-v14-run-manifest.md
30-v15-dataset-quality.md
31-v16-eval-suite.md
32-v17-run-registry.md
33-v18-registry-html.md
34-v19-registry-interactions.md
35-v20-registry-saved-views.md
36-v21-registry-annotations.md
37-v22-registry-leaderboards.md
38-v23-experiment-cards.md
39-v24-model-cards.md
40-v25-project-audit.md
41-v26-release-bundle.md
42-v27-release-gate.md
43-v28-generation-quality.md
44-v29-generation-quality-chain.md
45-v30-release-gate-generation-quality-policy.md
```

Release-governance records continue with the same global numbering:

```text
代码讲解记录_发布治理阶段/
46-v31-release-gate-policy-profiles.md
47-v32-release-gate-profile-comparison.md
48-v33-release-gate-profile-deltas.md
49-v34-configurable-release-gate-baseline.md
```

Evaluation-benchmark records start at v35:

```text
代码讲解记录_评估基准阶段/
50-v35-benchmark-eval-suite.md
51-v36-dataset-versioning.md
52-v37-baseline-model-comparison.md
53-v38-inference-safety-profile.md
54-v39-checkpoint-selector.md
55-v40-checkpoint-comparison-shortcuts.md
56-v41-side-by-side-generation.md
57-v42-pair-generation-artifacts.md
58-v43-pair-batch-comparison.md
59-v44-pair-batch-trends.md
60-v45-pair-batch-dashboard-links.md
61-v46-registry-pair-report-links.md
62-v47-registry-pair-delta-leaders.md
```

Project-maturity records start at v48:

```text
代码讲解记录_项目成熟度阶段/
63-v48-maturity-summary.md
64-v49-benchmark-scorecard.md
65-v50-benchmark-scorecard-drilldowns.md
66-v51-benchmark-rubric-scoring.md
67-v52-registry-benchmark-rubric-tracking.md
```

## Learning map

This project intentionally uses a simple character-level tokenizer so the GPT training loop is easy to see. The key idea is:

```text
input x:  人 工 智 能
target y: 工 智 能 正
```

The model sees the current and previous tokens, predicts the next token at every position, and uses cross entropy loss to update its parameters.

The chat wrapper does not change the model objective. It formats conversation turns into text, runs the same autoregressive generation loop, then trims the decoded result into an assistant reply.

The model report shows where parameters live and how tensor shapes move through embedding, attention, blocks, and logits.

The dashboard turns those artifacts into one local HTML report that can be opened without a server.

The comparison exporter reads multiple run directories, selects a baseline, and makes side-by-side model summaries with validation-loss, evaluation-loss, perplexity, parameter, tokenizer, model-signature, and dataset-version deltas.

The sampling lab compares how generation changes when temperature, top-k, and seed change.

The playground UI turns a run directory into a local browser surface for prompt controls, command snippets, sampling tables, and artifact links.

The playground server turns that browser surface into a local API client for `/api/health`, `/api/checkpoints`, `/api/checkpoint-compare`, `/api/model-info`, `/api/generate`, `/api/generate-pair`, and `/api/generate-pair-artifact`, with local request limits, selected checkpoint routing, side-by-side generation, checkpoint comparison shortcuts, saved pair artifacts, and JSONL inference logs.

The checkpoint comparison layer turns selectable checkpoints into a small local comparison table with file status, tokenizer readiness, parameter/dataset deltas, model-info links, and one-click selection inside the playground.

The side-by-side generation layer sends the same prompt and sampling settings to two selected checkpoints, returns left/right outputs with a compact comparison summary, and records the pair request in JSONL.

The persisted pair artifact layer saves side-by-side generation responses as local JSON/HTML files, links them from the playground, and records the artifact paths in the inference request log.

The fixed prompt pair batch layer runs the same prompt suite across two checkpoints and writes JSON/CSV/Markdown/HTML reports with per-case equality flags and character deltas.

The pair batch trend layer compares multiple saved pair batch reports, tracks equality variants and maximum deltas per case, and writes JSON/CSV/Markdown/HTML trend reports.

The pair batch dashboard/playground link layer surfaces saved pair batch and trend reports in dashboard and playground artifact sections so review starts from one local HTML page.

The registry pair report link layer carries those pair batch/trend summaries into the multi-run registry so many experiments can be scanned and opened from one index.

The registry pair delta leader layer aggregates pair batch case deltas across runs and highlights the largest generated-character differences in the registry HTML report.

The maturity summary layer summarizes v1-v48 into capability areas, phase coverage, registry context, and recommendations so future work can move by project maturity instead of tiny report-link increments.

The benchmark scorecard layer consolidates eval suite coverage, generation quality, pair consistency, pair delta stability, evidence completeness, and registry context into one run-level scorecard.

The benchmark scorecard drilldown layer groups case-level evidence by task type and difficulty, exports those group scores, and points reviewers at the weakest benchmark slices.

The benchmark rubric scoring layer adds per-prompt correctness checks, explicit required/forbidden terms, task-shape checks, weakest-case summaries, and a rubric CSV export.

The registry benchmark rubric layer carries those correctness scores into multi-run registry views, ranking runs by rubric average and surfacing correctness regressions.

The dataset preparation layer makes the training corpus explicit, inspectable, and reusable across runs.

The dataset versioning layer gives prepared corpora stable dataset ids, version directories, fingerprints, source roots, output links, and browser-readable dataset version reports.

The run manifest makes each training run easier to reproduce by saving code version, environment, data source, model config, metrics, and artifact inventory together.

The dataset quality layer adds a stable corpus fingerprint plus lightweight checks for duplicate files, tiny sources, and repeated lines.

The eval suite layer runs a fixed benchmark prompt set against a checkpoint and saves comparable JSON/CSV/SVG/HTML outputs with suite metadata, task types, difficulty, tags, and expected behavior.

The generation quality layer reads eval suite or sampling outputs and flags short, repetitive, low-diversity, or prompt-echo generations.

The generation quality evidence-chain layer carries that status into the run registry, model card, and project audit so release-style review can see generation quality readiness.

The run registry layer indexes multiple run directories so experiments can be scanned by commit, data fingerprint, quality status, eval suite coverage, metrics, artifact count, notes, tags, best-val rank, loss delta, a leaderboard, an interactive local HTML table, shareable URL state, and visible-row CSV export.

The experiment card layer turns one run into a compact JSON/Markdown/HTML summary for review, handoff, or portfolio use.

The model card layer turns a registry plus experiment cards into a project-level JSON/Markdown/HTML summary for presentation and model-family review.

The project audit layer checks whether the registry/model-card evidence is complete enough for release-style review.

The release bundle layer packages registry, model card, and audit evidence into one handoff report.

The release gate layer reads that bundle and turns release readiness into an automated pass/warn/fail decision for local scripts or CI.

The release gate generation-quality policy layer explicitly requires clean generation-quality audit checks before a release bundle can be approved.

The release gate policy profile layer gives the same gate named operating modes: `standard`, `review`, `strict`, and `legacy`.

The release gate profile comparison layer turns those modes into a matrix report, so one or more release bundles can be reviewed across several policy profiles at once.

The release gate profile delta layer explains why compared profiles disagree with the baseline by naming added/removed failed and warned checks.

The configurable release gate baseline layer lets profile delta explanations use an explicit baseline profile instead of always using the first selected profile.

Next useful extensions:

- Train on a larger Chinese corpus.
- Add dataset cards that summarize intended use, source limits, quality status, and version history.
- Add streaming token output for the playground server.
- Add registry-to-scorecard comparison reports that explain why rubric scores changed case by case.
- Compare from-scratch training with LoRA fine-tuning of an open model.
