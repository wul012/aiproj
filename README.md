# MiniGPT From Scratch

A PyTorch practice project for building a tiny character-level GPT language model.

## Current version

Version 2 is a resumable MiniGPT learning project with source code, tests, code explanations, and archived verification screenshots:

- Python project layout with `src`, `scripts`, `tests`, `data`, `.github/workflows`, `代码讲解记录`, and `a/<version>` archive directories
- Character-level tokenizer for turning Chinese text into token ids
- Dataset helpers for train/validation split and next-token batch sampling
- Transformer decoder with causal self-attention, multi-head attention, MLP blocks, residual connections, LayerNorm, and tied token embedding/output weights
- Training script with configurable model size, batch size, context window, learning rate, evaluation interval, and CPU/CUDA device selection
- Resumable training with `--resume`, optimizer-state checkpointing, and target-step continuation
- Training artifact output: `metrics.jsonl`, `history_summary.json`, `loss_curve.svg`, and `sample.txt`
- Generation script with checkpoint loading, prompt encoding, temperature sampling, and top-k sampling
- Generation script can write output to a file with `--out`
- History plotting script for rebuilding the loss curve from `metrics.jsonl`
- Sample Chinese training corpus for first-run experiments
- Unit tests for tokenizer, dataset sampling, history artifacts, model forward/loss, and generation shape
- Code explanation records for tokenizer/dataset, model core, train/generate scripts, tests/docs, and v2 training artifacts
- First and second version verification archives with key screenshots and command explanations
- GitHub Actions workflow for syntax checks and unit tests

## Version tags

Published tags:

```text
v1.0.0  MiniGPT v1 initial learning project
v2.0.0  MiniGPT v2 training artifacts
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
│   │   │   ├── 01-project-tree.png
│   │   │   ├── 02-unit-tests.png
│   │   │   ├── 03-train-smoke.png
│   │   │   ├── 04-generate-smoke.png
│   │   │   └── 05-code-explanation-check.png
│   │   └── 解释/
│   │       └── 说明.md
│   └── 2/
│       ├── 图片/
│       └── 解释/
│           └── 说明.md
├── data/
│   └── sample_zh.txt
├── scripts/
│   ├── generate.py
│   ├── plot_history.py
│   └── train.py
├── src/
│   └── minigpt/
│       ├── __init__.py
│       ├── dataset.py
│       ├── history.py
│       ├── model.py
│       └── tokenizer.py
├── tests/
│   ├── test_dataset.py
│   ├── test_history.py
│   ├── test_model.py
│   └── test_tokenizer.py
├── 代码讲解记录/
│   ├── README.md
│   ├── 01-tokenizer-and-dataset.md
│   ├── 02-model-core.md
│   ├── 03-train-generate.md
│   ├── 04-tests-docs.md
│   ├── 05-v2-training-artifacts.md
│   └── 06-version-2-tests-docs.md
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

## Generate

```powershell
python scripts/generate.py --prompt "人工智能" --max-new-tokens 120
```

Write generated text to a file:

```powershell
python scripts/generate.py --prompt "人工智能" --max-new-tokens 120 --out runs/minigpt/generated.txt
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
```

## Learning map

This project intentionally uses a simple character-level tokenizer so the GPT training loop is easy to see. The key idea is:

```text
input x:  人 工 智 能
target y: 工 智 能 正
```

The model sees the current and previous tokens, predicts the next token at every position, and uses cross entropy loss to update its parameters.

Next useful extensions:

- Replace character tokenization with BPE tokenization.
- Train on a larger Chinese corpus.
- Add a BPE tokenizer.
- Add a simple Web UI.
- Compare from-scratch training with LoRA fine-tuning of an open model.
