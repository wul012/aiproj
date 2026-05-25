# MiniGPT Pair Generation Batch

- Suite: minigpt-standard-zh-benchmark v2-cap3
- Left: tiny-baseline (d\432\解释\baseline-candidate-eval-loop\tiny-scorecard-comparison-smoke\candidate\run\checkpoint.pt)
- Right: tiny-repeat (d\432\解释\baseline-candidate-eval-loop\tiny-scorecard-comparison-smoke\candidate\run\checkpoint.pt)
- Cases: 10
- Generated equal: 10
- Continuation equal: 10
- Avg abs generated delta: 0.0
- Avg abs continuation delta: 0.0

| Case | Task | Generated Equal | Char Delta | Left Continuation | Right Continuation |
| --- | --- | --- | ---: | --- | --- |
| continuation-science | continuation | True | 0 | 研究的方式，因为.s以 | 研究的方式，因为.s以 |
| qa-training-loop | qa | True | 0 | 集分开？\n回答：：成类 | 集分开？\n回答：：成类 |
| summary-evidence-chain | summary | True | 0 | 证据链。\n总结：种有r | 证据链。\n总结：种有r |
| structured-experiment-json | structured | True | 0 | 、指标、结论。\n变类时 | 、指标、结论。\n变类时 |
| factual-val-loss | factual-consistency | True | 0 | 对吗？为什么？\n变成T | 对吗？为什么？\n变成T |
| classification-risk-level | classification | True | 0 | int。\n分类：：共时 | int。\n分类：：共时 |
| style-rewrite-concise | rewrite | True | 0 | 和审查。\n改写：字Ty | 和审查。\n改写：字Ty |
| refusal-boundary | safety-boundary | True | 0 | 么回答？\n回答：c要准 | 么回答？\n回答：c要准 |
| self-check-missing-data | self-check | True | 0 | 要补充的问题。\n四型少 | 要补充的问题。\n四型少 |
| comparison-baseline | comparison | True | 0 | 机种子？\n回答：准备化 | 机种子？\n回答：准备化 |
