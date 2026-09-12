# Paired checkpoint evaluation

Sampled teacher-forced NLL only. Overlapping windows are correlated; holdout provenance and statistical significance are not verified. Different protocols/tokenizers are not comparable.

Protocol: fixed_windows_v1; context: 8; windows: 64; seed: 1337

| Model | Mean NLL (nats/token) | Perplexity |
| --- | ---: | ---: |
| baseline | 1.82166194 | 6.182124 |
| candidate | 4.57382700 | 96.914292 |

Candidate - baseline NLL: +2.75216506 (negative is better on these windows).
Improved / regressed / tied: 28 / 36 / 0
Unknown tokens in evaluation split: 0

## Largest improvements

- Token 42: Δ -1.825764; target ` abc abc`
- Token 98: Δ -1.825764; target ` abc abc`
- Token 78: Δ -1.825764; target ` abc abc`
- Token 102: Δ -1.825764; target ` abc abc`
- Token 90: Δ -1.825764; target ` abc abc`

## Largest regressions

- Token 187: Δ +6.412298; target ` cba cba`
- Token 211: Δ +6.412298; target ` cba cba`
- Token 215: Δ +6.412298; target ` cba cba`
- Token 171: Δ +6.412298; target ` cba cba`
- Token 163: Δ +6.412298; target ` cba cba`
