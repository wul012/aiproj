# Model Training And Evaluation

The model training path is still the educational core of MiniGPT. It includes data preparation, tokenizer experiments, tiny GPT training, evaluation, generation checks, benchmark scorecards, holdout comparisons, and model capability diagnostics.

Important terms:

- `training` means producing or replaying a tiny model run with explicit configuration and artifacts.
- `evaluation` means reading model outputs, holdout rows, benchmark scorecards, or capability diagnostics without overstating production quality.
- `holdout` evidence is useful for comparison, but it is not enough by itself to claim a production-ready model.

Late-stage governance should not hide the model layer. After several publication receipt versions, the project should periodically return to model capability validation such as required-term coverage, loss signal bridge checks, decoder anchor distribution, unassisted repair, or exact surface repair.

See [Model capability cadence](model-capability-cadence.md) for the maintenance rule that keeps governance and readability work from replacing real model checks.
