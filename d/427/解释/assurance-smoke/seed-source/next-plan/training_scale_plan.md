# MiniGPT training scale plan

- Generated: `2026-05-25T06:16:09Z`
- Scale tier: `small`
- Dataset: `assurance-smoke` / `v292-smoke`
- Suite: `builtin:standard-zh`
- Sources: `1`
- Characters: `5760`
- Quality: `warn` with `1` warnings
- Variants file: `D:\aiproj\d\427\解释\assurance-smoke\seed-source\next-plan\training_scale_variants.json`

## Variant Matrix

| Variant | Config | Token budget | Corpus passes | Purpose |
| --- | --- | --- | --- | --- |
| scale-smoke | iters=50, batch=8, block=64, layers=2, heads=2, embd=64, seed=1337 | 25600 | 4.444 | Fast smoke run for checking the corpus and pipeline before spending time on training. |

## Batch Command

`D:\python\python.exe D:\aiproj\scripts\run_training_portfolio_batch.py D:\aiproj\d\427\解释\assurance-smoke\seed-source\corpus.txt --variants D:\aiproj\d\427\解释\assurance-smoke\seed-source\next-plan\training_scale_variants.json --out-root D:\aiproj\d\427\解释\assurance-smoke\seed-source\batch --dataset-name assurance-smoke --baseline scale-smoke --suite-name standard-zh`

## Recommendations

- Run the smoke variant first, then hand the generated training_scale_variants.json to the v69 batch runner.
- The corpus is small; compare baseline runs, but collect more Chinese text before trusting capability changes.
- Inspect dataset quality warnings before executing the extended training variant.
- The largest planned token budget is 25600 tokens in `scale-smoke`.

## Quality Issues

- `low_unique_ratio`: Unique-character ratio is low; the corpus may contain too much repetition.
- `repeated_line`: A normalized line appears multiple times.
