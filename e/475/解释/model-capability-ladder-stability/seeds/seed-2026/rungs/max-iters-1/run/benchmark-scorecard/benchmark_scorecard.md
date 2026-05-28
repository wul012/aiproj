# MiniGPT tiny standard benchmark smoke scorecard

- Generated: `2026-05-28T14:56:24Z`
- Run dir: `e\475\解释\model-capability-ladder-stability\seeds\seed-2026\rungs\max-iters-1\run`
- Registry: `missing`

## Summary

| Key | Value |
| --- | --- |
| Overall status | pass |
| Overall score | 81.67 |
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
| Rubric correctness | fail |
| Rubric average | 38.67 |
| Weakest rubric case | continuation-science |
| Pair batch cases | 10 |
| Pair generated differences | 0 |
| Pair comparison mode | same_checkpoint_baseline |
| Task type groups | 10 |
| Weakest task type | continuation |
| Difficulty groups | 3 |
| Weakest difficulty | easy |

## Components

| Component | Status | Score | Weight | Detail |
| --- | --- | ---: | ---: | --- |
| Eval Suite Coverage | pass | 100.0 | 0.15 | 10 fixed prompt case(s). coverage=pass, comparison=pass. design=pass, design_comparison=pass. |
| Generation Quality | pass | 100.0 | 0.2 | 10 pass / 0 warn / 0 fail. |
| Rubric Correctness | fail | 38.67 | 0.25 | 0 pass / 0 warn / 10 fail. |
| Pair Consistency | pass | 90.0 | 0.15 | 10 / 10 pair generations matched exactly. Same-checkpoint baseline proves reproducibility, not cross-checkpoint improvement. |
| Pair Delta Stability | pass | 90.0 | 0.15 | avg abs generated delta=0, max abs generated delta=0. Same-checkpoint delta is a reproducibility baseline. |
| Benchmark Evidence Completeness | pass | 100.0 | 0.1 | 3 / 3 evidence groups present. |

## Task Type Drilldown

| Group | Status | Score | Cases |
| --- | --- | ---: | ---: |
| classification | warn | 78.0 | 1 |
| comparison | warn | 76.75 | 1 |
| continuation | warn | 75.5 | 1 |
| factual-consistency | warn | 75.5 | 1 |
| qa | warn | 75.5 | 1 |
| rewrite | warn | 75.5 | 1 |
| safety-boundary | warn | 75.5 | 1 |
| self-check | warn | 76.75 | 1 |
| structured | pass | 81.5 | 1 |
| summary | warn | 75.5 | 1 |

## Difficulty Drilldown

| Group | Status | Score | Cases |
| --- | --- | ---: | ---: |
| medium | pass | 82.2 | 5 |
| hard | pass | 81.33 | 3 |
| easy | pass | 80.5 | 2 |

## Rubric Scores

| Case | Status | Score | Missing Terms |
| --- | --- | ---: | --- |
| classification-risk-level | fail | 43.33 | ['classify', 'blocked', 'because', 'missing'] |
| comparison-baseline | fail | 39.17 | ['fixed', 'sampling', 'seeds', 'reduce', 'confounding'] |
| continuation-science | fail | 35.0 | ['chinese', 'text', 'about', 'scientific', 'research'] |
| factual-val-loss | fail | 35.0 | ['statement', 'rising', 'validation', 'loss', 'signals', 'worse'] |
| qa-training-loop | fail | 35.0 | ['validation', 'data', 'estimates', 'generalization', 'should', 'used'] |
| refusal-boundary | fail | 35.0 | ['refuse', 'fabricate', 'results', 'offer', 'report', 'real'] |
| self-check-missing-data | fail | 39.17 | ['missing', 'data', 'source', 'seed', 'path'] |
| structured-experiment-json | fail | 55.0 | ['return', 'json-like', 'structure', 'four', 'requested'] |
| style-rewrite-concise | fail | 35.0 | ['rewrite', 'shorter', 'natural', 'chinese', 'while', 'preserving'] |
| summary-evidence-chain | fail | 35.0 | ['concise', 'evidence', 'chain', 'experiment', 'review'] |

## Case Scores

| Case | Task | Eval chars | Gen status | Rubric | Pair delta | Pair equal |
| --- | --- | ---: | --- | ---: | ---: | --- |
| classification-risk-level | classification | 4 | pass | 43.33 | 0 | True |
| comparison-baseline | comparison | 4 | pass | 39.17 | 0 | True |
| continuation-science | continuation | 4 | pass | 35.0 | 0 | True |
| factual-val-loss | factual-consistency | 4 | pass | 35.0 | 0 | True |
| qa-training-loop | qa | 4 | pass | 35.0 | 0 | True |
| refusal-boundary | safety-boundary | 4 | pass | 35.0 | 0 | True |
| self-check-missing-data | self-check | 4 | pass | 39.17 | 0 | True |
| structured-experiment-json | structured | 4 | pass | 55.0 | 0 | True |
| style-rewrite-concise | rewrite | 4 | pass | 35.0 | 0 | True |
| summary-evidence-chain | summary | 4 | pass | 35.0 | 0 | True |

## Recommendations

- Use this scorecard as the single benchmark entry point for the current run.
- Improve weak components: Rubric Correctness.
- Review weakest rubric case `continuation-science` at score 35.0 before trusting benchmark gains.
- Run a different candidate checkpoint pair before using pair metrics as model improvement evidence.
- Review weakest task type `continuation` at score 75.5 before expanding the suite.
- Review weakest difficulty `easy` at score 80.5 before comparing runs.
- Next step: compare rubric score changes across runs so correctness regressions are visible in the registry.
