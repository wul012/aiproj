# Per-corpus checkpoint comparison

Macro: equal corpus weight. Weighted: declared positive weights applied to corpus mean NLL, not perplexity or observed token counts.

Same paired windows within each corpus; no cross-corpus concatenation. Declared weights are policy, not measured traffic. Overlapping windows are correlated; holdout provenance/significance are not verified.

| Corpus | Weight | Windows | Baseline NLL | Candidate NLL | Delta |
| --- | ---: | ---: | ---: | ---: | ---: |
| forward | 9 | 16 | 1.826294 | 0.012370 | -1.813925 |
| reverse | 1 | 16 | 1.810937 | 8.202998 | +6.392061 |

- Equal-corpus macro NLL: 1.818616 → 4.107684; delta +2.289068.
  Perplexity: 6.163321306381399 → 60.80571162743327.
- Declared-weighted NLL: 1.824759 → 0.831432; delta -0.993326.
  Perplexity: 6.201298753438478 → 2.2966060801347576.
- Regressed corpora: reverse.

**Weighted total improves, but at least one corpus regresses. Do not hide this behind the total.**

---

## Corpus: forward

### Paired windows

Sampled teacher-forced NLL only. Overlapping windows are correlated; holdout provenance and statistical significance are not verified. Different protocols/tokenizers are not comparable.

Protocol: fixed_windows_v1; context: 8; windows: 16; seed: 1337

| Model | Mean NLL (nats/token) | Perplexity |
| --- | ---: | ---: |
| baseline | 1.82629448 | 6.210830 |
| candidate | 0.01236959 | 1.012446 |

Candidate - baseline NLL: -1.81392489 (negative is better on these windows).
Improved / regressed / tied: 16 / 0 / 0
Unknown tokens in evaluation split: 0

#### Largest improvements

- Token 90: Δ -1.825764; target ` abc abc`
- Token 46: Δ -1.825764; target ` abc abc`
- Token 74: Δ -1.825764; target ` abc abc`
- Token 42: Δ -1.825764; target ` abc abc`
- Token 50: Δ -1.825764; target ` abc abc`

#### Largest regressions

- None beyond the numerical tie tolerance.


---

## Corpus: reverse

### Paired windows

Sampled teacher-forced NLL only. Overlapping windows are correlated; holdout provenance and statistical significance are not verified. Different protocols/tokenizers are not comparable.

Protocol: fixed_windows_v1; context: 8; windows: 16; seed: 1337

| Model | Mean NLL (nats/token) | Perplexity |
| --- | ---: | ---: |
| baseline | 1.81093713 | 6.116176 |
| candidate | 8.20299786 | 3651.881756 |

Candidate - baseline NLL: +6.39206073 (negative is better on these windows).
Improved / regressed / tied: 0 / 16 / 0
Unknown tokens in evaluation split: 0

#### Largest improvements

- None beyond the numerical tie tolerance.

#### Largest regressions

- Token 90: Δ +6.412298; target ` cba cba`
- Token 46: Δ +6.412298; target ` cba cba`
- Token 74: Δ +6.412298; target ` cba cba`
- Token 42: Δ +6.412298; target ` cba cba`
- Token 50: Δ +6.412298; target ` cba cba`
