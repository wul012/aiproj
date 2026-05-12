# MiniGPT From Scratch

A PyTorch practice project for building and inspecting a tiny GPT language model.

## Current version

Version 30 is a MiniGPT learning project with release gate generation-quality policy, generation quality evidence-chain integration, generation quality reports, release gates, release evidence bundles, project audit reports, generated model cards, generated experiment cards, registry loss leaderboards and run rankings, run notes and tags in the registry, shareable and exportable registry HTML views, an interactive run registry HTML report, registry indexing for experiments, a fixed prompt evaluation suite, dataset quality checks and fingerprints, run manifests for experiment reproducibility, dataset preparation and reporting, a local playground server, a static playground Web UI, a sampling lab, multi-run comparison, a static experiment dashboard, model architecture reports, a tiny chat wrapper, next-token prediction inspection, evaluation reports, attention inspection, resumable training, character/BPE tokenizers, source code, tests, code explanations, and archived verification screenshots:

- Python project layout with `src`, `scripts`, `tests`, `data`, `.github/workflows`, `代码讲解记录`, and `a/<version>` archive directories
- Character-level tokenizer for turning Chinese text into token ids
- Optional character-seeded BPE tokenizer for understanding subword merge rules
- Tokenizer inspection script for comparing char and BPE tokenization
- Dataset preparation script for merging multiple `.txt` files and exporting dataset reports
- Dataset quality report with corpus fingerprint, duplicate-source checks, tiny/empty source warnings, repeated-line hints, JSON output, and SVG summary
- Run manifest writer that records Git metadata, environment, data source, model config, metrics, and artifact inventory for each training run
- Fixed prompt evaluation suite for running the same prompts against different checkpoints and exporting JSON/CSV/SVG reports
- Generation quality analyzer that reads `eval_suite.json` or `sample_lab.json`, checks length/diversity/repetition/prompt echo, and writes `generation_quality.json`, `generation_quality.csv`, `generation_quality.md`, `generation_quality.svg`, and `generation_quality.html`
- Generation quality evidence-chain integration across run registry, model card, and project audit, so generation quality status can affect release-style review
- Run registry builder that indexes multiple run directories, manifests, data fingerprints, quality status, eval suite summaries, metrics, and artifacts
- Run registry HTML report for browsing many experiments, opening dashboard/manifest/eval links, and scanning quality/fingerprint status in a browser
- Registry HTML controls for search, quality filtering, sorting, direction toggling, and visible-row counts
- Registry HTML view state in the URL plus visible-row CSV export for sharing and downstream analysis
- Optional `run_notes.json` annotations with note text, tags, tag counts, CSV columns, SVG summary text, and searchable HTML chips
- Registry best-val leaderboard with per-run rank, loss delta from the current best run, CSV columns, SVG labels, and an HTML leaderboard section
- Experiment card exporter that summarizes one run into `experiment_card.json`, `experiment_card.md`, and `experiment_card.html`, with registry rank, notes, data quality, training, evaluation, artifact, and recommendation sections
- Model card exporter that summarizes a registry and experiment cards into `model_card.json`, `model_card.md`, and `model_card.html`, with intended use, limitations, top runs, coverage, and recommendations
- Project audit exporter that checks registry/model-card readiness and writes `project_audit.json`, `project_audit.md`, and `project_audit.html` with pass/warn/fail checks, score, and recommendations
- Release bundle exporter that combines registry, model card, and project audit evidence into `release_bundle.json`, `release_bundle.md`, and `release_bundle.html`
- Release gate checker that reads `release_bundle.json`, applies a strict pass/warn/fail policy, writes `gate_report.json`, `gate_report.md`, and `gate_report.html`, and exits non-zero when the release is blocked
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
- Playground server that serves the UI and exposes `/api/health` plus `/api/generate` for local live generation
- Run comparison script that compares multiple experiments and exports JSON/CSV/SVG summaries
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
- Unit tests for tokenizer, dataset preparation, dataset quality, fixed prompt eval suites, generation quality reports, generation quality evidence-chain integration, run registry, run manifest generation, dataset sampling, history artifacts, model forward/loss, generation shape, prediction inspection, chat prompt handling, model reports, dashboard export, run comparison, sampling lab, playground UI export, playground server API, release bundles, release gates, and release gate generation-quality policy
- Code explanation records for tokenizer/dataset, model core, train/generate scripts, tests/docs, training artifacts, BPE, attention, prediction/evaluation, chat wrapper, model reports, dashboard export, run comparison, sampling lab, playground UI, playground server, dataset preparation, run manifests, dataset quality, eval suites, generation quality reports, generation quality evidence-chain integration, run registry, registry HTML reporting, registry interaction controls, shareable registry views, registry annotations, registry leaderboards, experiment cards, model cards, project audits, release bundles, release gates, and release gate generation-quality policy
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
│   └── 30/
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
│   ├── test_release_gate.py
│   ├── test_sampling.py
│   ├── test_server.py
│   └── test_tokenizer.py
├── 代码讲解记录/
│   ├── README.md
│   ├── 01-tokenizer-and-dataset.md
│   ├── 02-model-core.md
│   ├── 03-train-generate.md
│   ├── 04-tests-docs.md
│   ├── 05-v2-training-artifacts.md
│   ├── 06-version-2-tests-docs.md
│   ├── 07-v3-bpe-tokenizer.md
│   ├── 08-version-3-tests-docs.md
│   ├── 09-v4-attention-inspection.md
│   ├── 10-version-4-tests-docs.md
│   ├── 11-v5-prediction-evaluation.md
│   ├── 12-version-5-tests-docs.md
│   ├── 13-v6-chat-wrapper.md
│   ├── 14-version-6-tests-docs.md
│   ├── 15-v7-model-report.md
│   ├── 16-version-7-tests-docs.md
│   ├── 17-v8-dashboard.md
│   ├── 18-version-8-tests-docs.md
│   ├── 19-v9-run-comparison.md
│   ├── 20-version-9-tests-docs.md
│   ├── 21-v10-sampling-lab.md
│   ├── 22-version-10-tests-docs.md
│   ├── 23-v11-playground-ui.md
│   ├── 24-version-11-tests-docs.md
│   ├── 25-v12-playground-server.md
│   ├── 26-version-12-tests-docs.md
│   ├── 27-v13-dataset-preparation.md
│   ├── 28-version-13-tests-docs.md
│   ├── 29-v14-run-manifest.md
│   ├── 30-v15-dataset-quality.md
│   ├── 31-v16-eval-suite.md
│   ├── 32-v17-run-registry.md
│   ├── 33-v18-registry-html.md
│   ├── 34-v19-registry-interactions.md
│   ├── 35-v20-registry-saved-views.md
│   ├── 36-v21-registry-annotations.md
│   ├── 37-v22-registry-leaderboards.md
│   ├── 38-v23-experiment-cards.md
│   ├── 39-v24-model-cards.md
│   ├── 40-v25-project-audit.md
│   └── 41-v26-release-bundle.md
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

Run the fixed prompt evaluation suite:

```powershell
python scripts/eval_suite.py --checkpoint runs/minigpt/checkpoint.pt --suite data/eval_prompts.json
```

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

Train from a prepared corpus:

```powershell
python scripts/train.py --prepared-data runs/dataset/corpus.txt --out-dir runs/minigpt
```

Build a static playground UI:

```powershell
python scripts/build_playground.py --run-dir runs/minigpt
```

Serve the playground with a local generation API:

```powershell
python scripts/serve_playground.py --run-dir runs/minigpt --device cpu
```

Compare multiple run directories:

```powershell
python scripts/compare_runs.py runs/tiny runs/wide --name tiny --name wide --out-dir runs/comparison
```

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
python scripts/check_release_gate.py --bundle runs/release-bundle/release_bundle.json --out-dir runs/release-gate --min-audit-score 90 --min-ready-runs 1
```

The output directory contains `gate_report.json`, `gate_report.md`, and `gate_report.html`. The command exits with code `1` when the release is blocked, and `--fail-on-warn` can also make warning states fail CI.

By default the release gate also requires the project audit to include passing `generation_quality` and `non_pass_generation_quality` checks. Use `--allow-missing-generation-quality` only when checking legacy release bundles that predate v29/v30 generation-quality evidence.

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

The project keeps real command-output screenshots and explanations under:

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

## Code explanation records

Start here:

```text
代码讲解记录/README.md
```

Suggested reading order:

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

The comparison exporter reads multiple run directories and makes side-by-side experiment summaries.

The sampling lab compares how generation changes when temperature, top-k, and seed change.

The playground UI turns a run directory into a local browser surface for prompt controls, command snippets, sampling tables, and artifact links.

The playground server turns that browser surface into a local API client for `/api/health` and `/api/generate`.

The dataset preparation layer makes the training corpus explicit, inspectable, and reusable across runs.

The run manifest makes each training run easier to reproduce by saving code version, environment, data source, model config, metrics, and artifact inventory together.

The dataset quality layer adds a stable corpus fingerprint plus lightweight checks for duplicate files, tiny sources, and repeated lines.

The eval suite layer runs a fixed set of prompts against a checkpoint and saves comparable JSON/CSV/SVG outputs.

The generation quality layer reads eval suite or sampling outputs and flags short, repetitive, low-diversity, or prompt-echo generations.

The generation quality evidence-chain layer carries that status into the run registry, model card, and project audit so release-style review can see generation quality readiness.

The run registry layer indexes multiple run directories so experiments can be scanned by commit, data fingerprint, quality status, eval suite coverage, metrics, artifact count, notes, tags, best-val rank, loss delta, a leaderboard, an interactive local HTML table, shareable URL state, and visible-row CSV export.

The experiment card layer turns one run into a compact JSON/Markdown/HTML summary for review, handoff, or portfolio use.

The model card layer turns a registry plus experiment cards into a project-level JSON/Markdown/HTML summary for presentation and model-family review.

The project audit layer checks whether the registry/model-card evidence is complete enough for release-style review.

The release bundle layer packages registry, model card, and audit evidence into one handoff report.

The release gate layer reads that bundle and turns release readiness into an automated pass/warn/fail decision for local scripts or CI.

The release gate generation-quality policy layer explicitly requires clean generation-quality audit checks before a release bundle can be approved.

Next useful extensions:

- Train on a larger Chinese corpus.
- Add streaming token output for the playground server.
- Add release-gate policy profiles for strict portfolio release versus relaxed local exploration.
- Compare from-scratch training with LoRA fine-tuning of an open model.
