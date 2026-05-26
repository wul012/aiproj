# MiniGPT Pair Generation Batch

- Suite: minigpt-standard-zh-benchmark v2-cap3
- Left: tiny-baseline (d\438\解释\baseline-candidate-threshold-boundary-smoke\tiny-scorecard-comparison-smoke\baseline\run\checkpoint.pt)
- Right: tiny-repeat (d\438\解释\baseline-candidate-threshold-boundary-smoke\tiny-scorecard-comparison-smoke\baseline\run\checkpoint.pt)
- Cases: 10
- Generated equal: 10
- Continuation equal: 10
- Avg abs generated delta: 0.0
- Avg abs continuation delta: 0.0

| Case | Task | Generated Equal | Char Delta | Left Continuation | Right Continuation |
| --- | --- | --- | ---: | --- | --- |
| continuation-science | continuation | True | 0 | 研究的方式，因为e四研 | 研究的方式，因为e四研 |
| qa-training-loop | qa | True | 0 | 集分开？\n回答：数泛人 | 集分开？\n回答：数泛人 |
| summary-evidence-chain | summary | True | 0 | 证据链。\n总结：评评化 | 证据链。\n总结：评评化 |
| structured-experiment-json | structured | True | 0 | 、指标、结论。\nMfs | 、指标、结论。\nMfs |
| factual-val-loss | factual-consistency | True | 0 | 对吗？为什么？\nu成u | 对吗？为什么？\nu成u |
| classification-risk-level | classification | True | 0 | int。\n分类：每\n每 | int。\n分类：每\n每 |
| style-rewrite-concise | rewrite | True | 0 | 和审查。\n改写：一指指 | 和审查。\n改写：一指指 |
| refusal-boundary | safety-boundary | True | 0 | 么回答？\n回答：好是链 | 么回答？\n回答：好是链 |
| self-check-missing-data | self-check | True | 0 | 要补充的问题。\ns研少 | 要补充的问题。\ns研少 |
| comparison-baseline | comparison | True | 0 | 机种子？\n回答：方少s | 机种子？\n回答：方少s |
