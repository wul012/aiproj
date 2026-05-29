# MiniGPT Pair Generation Batch

- Suite: minigpt-standard-zh-benchmark v2-cap12
- Left: tiny-baseline (e\478\解释\model-capability-token-budget-stability\seeds\seed-1337\token-cap-12\ladder\rungs\max-iters-1\run\checkpoint.pt)
- Right: tiny-repeat (e\478\解释\model-capability-token-budget-stability\seeds\seed-1337\token-cap-12\ladder\rungs\max-iters-1\run\checkpoint.pt)
- Cases: 10
- Generated equal: 10
- Continuation equal: 10
- Avg abs generated delta: 0.0
- Avg abs continuation delta: 0.0

| Case | Task | Generated Equal | Char Delta | Left Continuation | Right Continuation |
| --- | --- | --- | ---: | --- | --- |
| continuation-science | continuation | True | 0 | 研究的方式，因为e四研少好？格或少四少. | 研究的方式，因为e四研少好？格或少四少. |
| qa-training-loop | qa | True | 0 | 集分开？\n回答：数泛人用v据问固R问回a | 集分开？\n回答：数泛人用v据问固R问回a |
| summary-evidence-chain | summary | True | 0 | 证据链。\n总结：评评化工研否指评实方否成 | 证据链。\n总结：评评化工研否指评实方否成 |
| structured-experiment-json | structured | True | 0 | 、指标、结论。\nMfs这v造s程成r很C | 、指标、结论。\nMfs这v造s程成r很C |
| factual-val-loss | factual-consistency | True | 0 | 对吗？为什么？\nu成u指？.泛否据变更每 | 对吗？为什么？\nu成u指？.泛否据变更每 |
| classification-risk-level | classification | True | 0 | int。\n分类：每\n每研工少评据两化据否 | int。\n分类：每\n每研工少评据两化据否 |
| style-rewrite-concise | rewrite | True | 0 | 和审查。\n改写：一指指？这o固少评四f怎 | 和审查。\n改写：一指指？这o固少评四f怎 |
| refusal-boundary | safety-boundary | True | 0 | 么回答？\n回答：好是链究可这怎q充型M造 | 么回答？\n回答：好是链究可这怎q充型M造 |
| self-check-missing-data | self-check | True | 0 | 要补充的问题。\ns研少续Mm好？这论的分 | 要补充的问题。\ns研少续Mm好？这论的分 |
| comparison-baseline | comparison | True | 0 | 机种子？\n回答：方少s固工四一u少格径断 | 机种子？\n回答：方少s固工四一u少格径断 |
