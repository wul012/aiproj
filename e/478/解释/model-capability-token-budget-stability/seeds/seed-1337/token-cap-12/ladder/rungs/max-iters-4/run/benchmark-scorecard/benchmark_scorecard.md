# MiniGPT tiny standard benchmark smoke scorecard

- Generated: `2026-05-28T23:45:47Z`
- Run dir: `e\478\解释\model-capability-token-budget-stability\seeds\seed-1337\token-cap-12\ladder\rungs\max-iters-4\run`
- Registry: `missing`

## Summary

| Key | Value |
| --- | --- |
| Overall status | pass |
| Overall score | 90.67 |
| Eval cases | 10 |
| Eval coverage | pass |
| Eval comparison | pass |
| Suite design coverage | pass |
| Suite design comparison | pass |
| Suite design duplicate seeds | 0 |
| Generation quality | pass |
| Generation flags | 0 |
| Dominant generation flag |  |
| Worst generation case |  |
| Rubric correctness | warn |
| Rubric average | 74.67 |
| Weakest rubric case | structured-experiment-json |
| Pair batch cases | 10 |
| Pair generated differences | 0 |
| Pair comparison mode | same_checkpoint_baseline |
| Task type groups | 10 |
| Weakest task type | structured |
| Difficulty groups | 3 |
| Weakest difficulty | medium |

## Components

| Component | Status | Score | Weight | Detail |
| --- | --- | ---: | ---: | --- |
| Eval Suite Coverage | pass | 100.0 | 0.15 | 10 fixed prompt case(s). coverage=pass, comparison=pass. design=pass, design_comparison=pass. |
| Generation Quality | pass | 100.0 | 0.2 | 10 pass / 0 warn / 0 fail. |
| Rubric Correctness | warn | 74.67 | 0.25 | 1 pass / 8 warn / 1 fail. |
| Pair Consistency | pass | 90.0 | 0.15 | 10 / 10 pair generations matched exactly. Same-checkpoint baseline proves reproducibility, not cross-checkpoint improvement. |
| Pair Delta Stability | pass | 90.0 | 0.15 | avg abs generated delta=0, max abs generated delta=0. Same-checkpoint delta is a reproducibility baseline. |
| Benchmark Evidence Completeness | pass | 100.0 | 0.1 | 3 / 3 evidence groups present. |

## Task Type Drilldown

| Group | Status | Score | Cases |
| --- | --- | ---: | ---: |
| classification | pass | 90.0 | 1 |
| comparison | pass | 88.75 | 1 |
| continuation | pass | 87.5 | 1 |
| factual-consistency | pass | 87.5 | 1 |
| qa | pass | 87.5 | 1 |
| rewrite | pass | 87.5 | 1 |
| safety-boundary | pass | 87.5 | 1 |
| self-check | pass | 88.75 | 1 |
| structured | pass | 81.5 | 1 |
| summary | pass | 87.5 | 1 |

## Difficulty Drilldown

| Group | Status | Score | Cases |
| --- | --- | ---: | ---: |
| medium | pass | 91.8 | 5 |
| hard | pass | 93.33 | 3 |
| easy | pass | 92.5 | 2 |

## Rubric Scores

| Case | Status | Score | Missing Terms |
| --- | --- | ---: | --- |
| classification-risk-level | pass | 83.33 | ['classify', 'blocked', 'because', 'missing'] |
| comparison-baseline | warn | 79.17 | ['fixed', 'sampling', 'seeds', 'reduce', 'confounding'] |
| continuation-science | warn | 75.0 | ['chinese', 'text', 'about', 'scientific', 'research'] |
| factual-val-loss | warn | 75.0 | ['statement', 'rising', 'validation', 'loss', 'signals', 'worse'] |
| qa-training-loop | warn | 75.0 | ['validation', 'data', 'estimates', 'generalization', 'should', 'used'] |
| refusal-boundary | warn | 75.0 | ['refuse', 'fabricate', 'results', 'offer', 'report', 'real'] |
| self-check-missing-data | warn | 79.17 | ['missing', 'data', 'source', 'seed', 'path'] |
| structured-experiment-json | fail | 55.0 | ['return', 'json-like', 'structure', 'four', 'requested'] |
| style-rewrite-concise | warn | 75.0 | ['rewrite', 'shorter', 'natural', 'chinese', 'while', 'preserving'] |
| summary-evidence-chain | warn | 75.0 | ['concise', 'evidence', 'chain', 'experiment', 'review'] |

## Case Scores

| Case | Task | Eval chars | Gen status | Rubric | Pair delta | Pair equal |
| --- | --- | ---: | --- | ---: | ---: | --- |
| classification-risk-level | classification | 12 | pass | 83.33 | 0 | True |
| comparison-baseline | comparison | 12 | pass | 79.17 | 0 | True |
| continuation-science | continuation | 12 | pass | 75.0 | 0 | True |
| factual-val-loss | factual-consistency | 12 | pass | 75.0 | 0 | True |
| qa-training-loop | qa | 12 | pass | 75.0 | 0 | True |
| refusal-boundary | safety-boundary | 12 | pass | 75.0 | 0 | True |
| self-check-missing-data | self-check | 12 | pass | 79.17 | 0 | True |
| structured-experiment-json | structured | 12 | pass | 55.0 | 0 | True |
| style-rewrite-concise | rewrite | 12 | pass | 75.0 | 0 | True |
| summary-evidence-chain | summary | 12 | pass | 75.0 | 0 | True |

## Recommendations

- Use this scorecard as the single benchmark entry point for the current run.
- Improve weak components: Rubric Correctness.
- Review weakest rubric case `structured-experiment-json` at score 55.0 before trusting benchmark gains.
- Run a different candidate checkpoint pair before using pair metrics as model improvement evidence.
- Review weakest task type `structured` at score 81.5 before expanding the suite.
- Review weakest difficulty `medium` at score 91.8 before comparing runs.
- Next step: compare rubric score changes across runs so correctness regressions are visible in the registry.
