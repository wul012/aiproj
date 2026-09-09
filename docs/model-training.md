# Model Training And Evaluation

The model training path is still the educational core of MiniGPT. It includes data preparation, tokenizer experiments, tiny GPT training, evaluation, generation checks, benchmark scorecards, holdout comparisons, and model capability diagnostics.

Important terms:

- `training` means producing or replaying a tiny model run with explicit configuration and artifacts.
- `evaluation` means reading model outputs, holdout rows, benchmark scorecards, or capability diagnostics without overstating production quality.
- `holdout` evidence is useful for comparison, but it is not enough by itself to claim a production-ready model.

Late-stage governance should not hide the model layer. After several publication receipt versions, the project should periodically return to model capability validation such as required-term coverage, loss signal bridge checks, decoder anchor distribution, unassisted repair, or exact surface repair.

See [Model capability cadence](model-capability-cadence.md) for the maintenance rule that keeps governance and readability work from replacing real model checks.

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
