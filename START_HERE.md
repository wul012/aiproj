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

Current README focus: **v1099 documentation template hardening**.

v1098 freezes overcrowded historical documentation directories and starts new sibling directories for model-governance explanations and runtime evidence. v1099 adds a reusable explanation template so future docs follow the same goal, boundary, entrypoint, output model, upstream evidence, checks, and test-evidence pattern.

## Where to look next

- `README.md` — full project overview and version map.
- `文档分流说明.md` — current documentation routing map.
- `src/minigpt/` — model, evaluation, reporting, and workflow code.
- `tests/` — behavior and report-shape tests.
- `e/` — v473-v1097 runtime screenshots and explanations.
- `f/` — v1098+ runtime screenshots and explanations.
- `代码讲解记录_模型能力阶段/` — v473-v1097 historical explanations.
- `代码讲解记录_模型治理阶段/` — v1098+ explanation home when a version needs a detailed explanation.
