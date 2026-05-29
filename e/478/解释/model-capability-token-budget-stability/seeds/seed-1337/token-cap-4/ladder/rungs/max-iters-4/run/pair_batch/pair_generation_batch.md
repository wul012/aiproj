# MiniGPT Pair Generation Batch

- Suite: minigpt-standard-zh-benchmark v2-cap4
- Left: tiny-baseline (e\478\解释\model-capability-token-budget-stability\seeds\seed-1337\token-cap-4\ladder\rungs\max-iters-4\run\checkpoint.pt)
- Right: tiny-repeat (e\478\解释\model-capability-token-budget-stability\seeds\seed-1337\token-cap-4\ladder\rungs\max-iters-4\run\checkpoint.pt)
- Cases: 10
- Generated equal: 10
- Continuation equal: 10
- Avg abs generated delta: 0.0
- Avg abs continuation delta: 0.0

| Case | Task | Generated Equal | Char Delta | Left Continuation | Right Continuation |
| --- | --- | --- | ---: | --- | --- |
| continuation-science | continuation | True | 0 | 研究的方式，因为e四研少 | 研究的方式，因为e四研少 |
| qa-training-loop | qa | True | 0 | 集分开？\n回答：数泛人用 | 集分开？\n回答：数泛人用 |
| summary-evidence-chain | summary | True | 0 | 证据链。\n总结：评评化工 | 证据链。\n总结：评评化工 |
| structured-experiment-json | structured | True | 0 | 、指标、结论。\nMfsn | 、指标、结论。\nMfsn |
| factual-val-loss | factual-consistency | True | 0 | 对吗？为什么？\nu成u指 | 对吗？为什么？\nu成u指 |
| classification-risk-level | classification | True | 0 | int。\n分类：每\n每研 | int。\n分类：每\n每研 |
| style-rewrite-concise | rewrite | True | 0 | 和审查。\n改写：一指指？ | 和审查。\n改写：一指指？ |
| refusal-boundary | safety-boundary | True | 0 | 么回答？\n回答：好是链究 | 么回答？\n回答：好是链究 |
| self-check-missing-data | self-check | True | 0 | 要补充的问题。\ns研少续 | 要补充的问题。\ns研少续 |
| comparison-baseline | comparison | True | 0 | 机种子？\n回答：方少s固 | 机种子？\n回答：方少s固 |
