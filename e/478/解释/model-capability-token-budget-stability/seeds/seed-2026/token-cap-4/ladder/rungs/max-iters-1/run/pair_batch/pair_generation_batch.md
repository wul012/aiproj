# MiniGPT Pair Generation Batch

- Suite: minigpt-standard-zh-benchmark v2-cap4
- Left: tiny-baseline (e\478\解释\model-capability-token-budget-stability\seeds\seed-2026\token-cap-4\ladder\rungs\max-iters-1\run\checkpoint.pt)
- Right: tiny-repeat (e\478\解释\model-capability-token-budget-stability\seeds\seed-2026\token-cap-4\ladder\rungs\max-iters-1\run\checkpoint.pt)
- Cases: 10
- Generated equal: 10
- Continuation equal: 10
- Avg abs generated delta: 0.0
- Avg abs continuation delta: 0.0

| Case | Task | Generated Equal | Char Delta | Left Continuation | Right Continuation |
| --- | --- | --- | ---: | --- | --- |
| continuation-science | continuation | True | 0 | 研究的方式，因为.s以很 | 研究的方式，因为.s以很 |
| qa-training-loop | qa | True | 0 | 集分开？\n回答：：成类少 | 集分开？\n回答：：成类少 |
| summary-evidence-chain | summary | True | 0 | 证据链。\n总结：种有r通 | 证据链。\n总结：种有r通 |
| structured-experiment-json | structured | True | 0 | 、指标、结论。\n变类时y | 、指标、结论。\n变类时y |
| factual-val-loss | factual-consistency | True | 0 | 对吗？为什么？\n变成T指 | 对吗？为什么？\n变成T指 |
| classification-risk-level | classification | True | 0 | int。\n分类：：共时. | int。\n分类：：共时. |
| style-rewrite-concise | rewrite | True | 0 | 和审查。\n改写：字Ty指 | 和审查。\n改写：字Ty指 |
| refusal-boundary | safety-boundary | True | 0 | 么回答？\n回答：c要准字 | 么回答？\n回答：c要准字 |
| self-check-missing-data | self-check | True | 0 | 要补充的问题。\n四型少通 | 要补充的问题。\n四型少通 |
| comparison-baseline | comparison | True | 0 | 机种子？\n回答：准备化归 | 机种子？\n回答：准备化归 |
