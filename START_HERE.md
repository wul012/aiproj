# Start Here: MiniGPT From Scratch

## What this project does

This repository is a PyTorch learning project for building, training, inspecting, and evaluating a small GPT-style language model from scratch.

It covers the full local learning path:

```text
tokenizer -> dataset -> transformer model -> training -> generation -> inspection -> evaluation -> reports
```

The project also keeps detailed versioned notes, screenshots, reports, and evidence archives so each stage can be reviewed later.

## Why it matters

This is not only a toy model repo. It is a structured AI engineering practice project.

The strongest parts are:

- A clear MiniGPT model learning path.
- Local evaluation and benchmark tooling.
- Dataset, experiment, model-card, release-readiness, and maturity-report evidence.
- Versioned documentation that explains what changed and why.

For a reader, the main value is seeing how a small model project can grow from basic training into a more disciplined evaluation and release workflow.

## How to run it

Start by reading the main `README.md`, then inspect the versioned explanation folders.

Typical workflow:

```powershell
python -m unittest discover
```

For specific training, evaluation, dashboard, or report commands, use the matching section in `README.md` because the project has many versioned workflows.

## Top technical highlights

1. **MiniGPT model core**
   - Tokenizer, causal self-attention, training, generation, and prediction inspection.

2. **Evaluation discipline**
   - Fixed prompt suites, generation-quality reports, benchmark scorecards, comparison reports, and maturity narratives.

3. **Evidence-first workflow**
   - Versioned screenshots, report artifacts, code explanations, and release/readiness gates make the project easier to audit.

## Latest version summary

Current README focus: **v226 eval-suite coverage readiness**.

v226 adds coverage evidence to fixed-prompt eval-suite reports. It separates small ad hoc suites from broader benchmark suites before making checkpoint-quality claims.

In simple terms: the project now asks not only “did the eval run?” but also “is this prompt suite representative enough for model comparison?”

## Where to look next

- `README.md` — full project overview and version map.
- `src/minigpt/` — model, evaluation, reporting, and workflow code.
- `tests/` — behavior and report-shape tests.
- `c/` — later-stage screenshots and evidence archives.
- `代码讲解记录_项目成熟度阶段/` — detailed version explanations.
