# MiniGPT From Scratch

A PyTorch practice project for building a tiny character-level GPT language model.

## Current version

Version 1 is a runnable MiniGPT learning project with source code, tests, code explanations, and archived verification screenshots:

- Python project layout with `src`, `scripts`, `tests`, `data`, `.github/workflows`, `代码讲解记录`, and `a/1` archive directories
- Character-level tokenizer for turning Chinese text into token ids
- Dataset helpers for train/validation split and next-token batch sampling
- Transformer decoder with causal self-attention, multi-head attention, MLP blocks, residual connections, LayerNorm, and tied token embedding/output weights
- Training script with configurable model size, batch size, context window, learning rate, evaluation interval, and CPU/CUDA device selection
- Generation script with checkpoint loading, prompt encoding, temperature sampling, and top-k sampling
- Sample Chinese training corpus for first-run experiments
- Unit tests for tokenizer, dataset sampling, model forward/loss, and generation shape
- Code explanation records for tokenizer/dataset, model core, train/generate scripts, and tests/docs
- First-round verification archive with key screenshots and command explanations
- GitHub Actions workflow for syntax checks and unit tests

## Project structure

```text
.
├── .github/
│   └── workflows/
│       └── ci.yml
├── a/
│   └── 1/
│       ├── 图片/
│       │   ├── 01-project-tree.png
│       │   ├── 02-unit-tests.png
│       │   ├── 03-train-smoke.png
│       │   ├── 04-generate-smoke.png
│       │   └── 05-code-explanation-check.png
│       └── 解释/
│           └── 说明.md
├── data/
│   └── sample_zh.txt
├── scripts/
│   ├── generate.py
│   └── train.py
├── src/
│   └── minigpt/
│       ├── __init__.py
│       ├── dataset.py
│       ├── model.py
│       └── tokenizer.py
├── tests/
│   ├── test_dataset.py
│   ├── test_model.py
│   └── test_tokenizer.py
├── 代码讲解记录/
│   ├── README.md
│   ├── 01-tokenizer-and-dataset.md
│   ├── 02-model-core.md
│   ├── 03-train-generate.md
│   └── 04-tests-docs.md
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
```

## Generate

```powershell
python scripts/generate.py --prompt "人工智能" --max-new-tokens 120
```

## Test

```powershell
python -B -m unittest discover -s tests -v
```

## Verification archive

The first version keeps real command-output screenshots and explanations under:

```text
a/1/图片
a/1/解释/说明.md
```

Screenshots:

- `01-project-tree.png`: project structure check
- `02-unit-tests.png`: unit test run
- `03-train-smoke.png`: real training smoke test
- `04-generate-smoke.png`: checkpoint loading and generation smoke test
- `05-code-explanation-check.png`: code explanation document check

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
- Add checkpoint resume.
- Add a simple Web UI.
- Compare from-scratch training with LoRA fine-tuning of an open model.
