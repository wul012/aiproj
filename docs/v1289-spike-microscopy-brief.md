# v1289 — spike microscopy: does the collapse tear the circuit?

Preregistered before any GPU run. Executed by Claude directly (ML lane).

## Question

v1287 discovered that grokked solutions are metastable under continued
training: train+val spike together and self-heal in 100–300 steps. v1288
proved the spikes are wd-driven (paired branch arms; S1=8/9 vs S0=0).
Both versions saw spikes only at 100-step eval resolution. v1289 puts the
committed spikes under a per-step microscope and asks the mechanism
question: **when val collapses, does the Fourier circuit in the number
embedding collapse with it, or does the circuit persist while the
solution's readout breaks?**

Both answers are live and mechanistically loaded:

- *Circuit persists* → spikes are shallow perturbations of a robust
  structure; wd's shove breaks calibration/readout, not the mechanism;
  recovery is cheap because nothing structural was lost. This would
  cohere with v1287's ladder purities climbing monotonically across
  snapshots that bracket spikes.
- *Circuit destroyed* → metastability is deep: wd periodically tears the
  structure down and recovery is a fast rebuild; purification would be
  reinterpreted as repeated partial rebuilds. This would strain v1287's
  slow-purification timescales — which is exactly why it must be tested,
  not assumed.

The banked "microscopic spike trigger" question is answered by the same
dense data as preregistered **secondary, non-verdict** readouts: per-step
train loss (the optimizer's actual objective, captured from the training
backward), gradient norm (captured free from the same backward), total
weight norm, and precursor lead time. They are non-verdict because any
precursor bar on a continuous drifting signal is bar-unstable by the
v1286 lesson; the verdict rides on the share-ratio dichotomy instead.

## P1 grounding (CPU, committed caches only — done before this freeze)

From the committed v1287 cache (`f/1287/解释/grok_purification_v1287/
phase_a_cache.pt`), episode extraction at bar 0.9 reproduces the v1287
census exactly: 9/11 cells spike post-grok; 1e-3/1337 and 8e-3/1337 are
clean. 24 committed post-grok episodes total. Two morphologies:

- **Deep single-row events**: e.g. 1e-3/1339 goes 12600: val 0.986 →
  12700: val 0.385 (train 0.799) → 12800: val 0.980. The entire collapse
  AND most of the recovery live *between* 100-step evals. Microscopy is
  genuinely needed; dense minima can only be deeper than committed row
  values (the committed rows are a subset of the dense grid).
- **A slow dip**: 1e-3/1338 drifts 0.952 → 0.892 over 700 steps
  (13000→13700), then snaps back to 0.971 in one row.

Budget arithmetic: one deterministic rerun per cell passes through all
its episode windows on the way; total 73,700 training steps for all 9
spiking cells, 15,620 dense-eval steps in 20 windows.

## Substrate and integrity (G0)

The microscopy must continue the ORIGINAL committed trajectories — same
Adam moments — so v1288-style branch arms (which restart optimizer
state) are unusable here. `train_to_grok` cannot export per-step
measurements, so v1289 reimplements its loop line-for-line
(`dense_run`): same `scaled_init(width, seed, 1.0, ·)`, same
`seed_everything` / `split_indices` / `make_grok_model` /
`load_state_dict` / AdamW construction order, same eval-then-update body,
same rounding. All added measurements are pure reads (`answer_accuracy`
is no-grad argmax; dropout=0.0 makes train/eval modes identical; no RNG
is consumed anywhere after init).

**G0 certificate**: every coarse row (every 100 steps, original cadence
and rounding) must match the committed v1287 curve bit-equal (≤1e-9 on
the rounded values) over the entire rerun range, and dense rows at
100-multiples must agree with the coarse rows. A single ULP of loop
divergence fires `reference_mismatch` → verdict `review`. This gate is
the proof that the reimplemented loop IS the original loop.

## Design

Cells: the 9 spiking v1287 cells. Windows: mechanically derived from the
committed episode list — for each post-grok episode `[s, e]` (episodes
with start ≥ t_gen), window `[s−400, e+300]` clamped to `[0, horizon]`,
overlapping/adjacent windows merged; rerun_end = last window end.

| lr | seed | rerun_end | windows |
|----|------|-----------|---------|
| 1e-3 | 1338 | 14000 | [13200,14000] |
| 1e-3 | 1339 | 25700 | [10900,11700] [12300,13000] [16900,17600] [25000,25700] |
| 2e-3 | 1337 | 5500 | [2200,2900] [4800,5500] |
| 2e-3 | 1338 | 8400 | [6200,6900] [7000,7700] [7900,8400] |
| 4e-3 | 1337 | 3700 | [1300,2000] [2600,3700] |
| 4e-3 | 1338 | 5400 | [1500,2200] [3400,4100] [4300,5400] |
| 4e-3 | 1339 | 3000 | [900,1600] [2100,3000] |
| 8e-3 | 1338 | 3500 | [1100,2300] [2800,3500] |
| 8e-3 | 1339 | 4500 | [3700,4500] |

Per dense step (every step inside a window): `train_acc`, `val_acc`
(same functions as the committed curve), full 48-bin embedding power
spectrum, total weight norm — all pre-update; plus `train_loss` and
`grad_norm` captured from the actual training backward at that step
(state-k loss producing state k+1; the final step of the last window has
no update, recorded as None).

### Episode extraction and qualification (mechanical, Phase B)

Dense episodes = maximal runs of `val < 0.9` at step resolution inside a
window (v1288's `episodes()` with `eval_every=1`). An episode qualifies
for the primary iff:

1. **interior**: starts strictly after the window start and ends
   strictly before the window end (start-truncated pre-grok tails and
   horizon-censored deaths are excluded — the two v1287 censored deaths
   are secondary-only by construction);
2. **baseline**: ≥30 healthy steps (`val ≥ 0.9`) among the ≤100 dense
   steps immediately before the episode start.

### Primary statistic and verdict ladder

Per qualified episode: `S_ep` = top-5 frequency set of the mean baseline
spectrum; share series = `set_share(power_t, S_ep)` smoothed with a
centered 5-step median filter; **r = (min smoothed share over the
episode) / (median smoothed share over the baseline)**. Labels:
`preserved` if r ≥ 0.8, `destroyed` if r ≤ 0.5, else `mid`.

**Deep** episodes: dense `min_val < deep_bar` (0.5). With n_pres /
n_dest / n_mid over deep episodes:

- `spike_preserves_circuit`: n_dest == 0 and n_pres > n_mid
- `spike_destroys_circuit`: n_pres == 0 and n_dest > n_mid
- `spike_mixed`: n_pres ≥ 1 and n_dest ≥ 1 (mixedness is a finding,
  cf. v1283)
- `review` otherwise (reason `mid_band`), or `insufficient_deep` if
  fewer than 3 deep qualified episodes.

Guaranteed-by-cache deep candidates at all grid bars (conditional on G0
and qualification): 1e-3/1339@12700 (committed 0.385, pre-row 0.986),
4e-3/1338@1900 (0.147, pre-row 0.999), 8e-3/1338@1500 (0.478, pre-row
0.989). min_deep = 3 is expected-satisfied but NOT structurally
guaranteed (dense baselines could fragment); `review/insufficient_deep`
is the honest, publishable fallback. Dense minima ≤ committed row minima
wherever a committed sub-bar row falls inside a window, so the deep set
can only grow relative to this floor.

### Gates

- **G0**: committed-curve bit-equality (above) + dense/coarse agreement
  at shared steps + finiteness (None allowed only at the no-update final
  step) → else `review` with reason.
- **G1**: all 9 cells present, window structure matches the config,
  every in-window step has a dense row → else `grid_incomplete`.
- **G2**: verdict label stable across deep_bar ∈ {0.5, 0.55, 0.6}
  (labels per episode are bar-independent; only deep membership moves)
  → else `review/bar_instability`.

### Secondary readouts (preregistered, non-verdict)

1. **Trigger/precursor**: t_loss_break = first dense step before the
   val break where train_loss exceeds baseline median + 20×MAD sustained
   5 steps (MAD=0 fallback: 10× median); lead = val_break − loss_break.
   Reported as a distribution; None = no detectable precursor.
2. **Shove size**: max grad_norm in episode / baseline median grad_norm.
3. **Norm**: min total norm in episode / baseline median norm.
4. **Hidden depth**: dense min_val vs committed 100-res min over the
   same span (quantifies between-eval censoring; an episode with NO
   committed row inside it is a fully hidden spike).
5. **Fall/recovery shape**: argmin−start+1 and end+1−argmin at step
   resolution.
6. **Rotation-during-spike**: top-5 set from ≥30 healthy post-episode
   steps vs `S_ep` (partially executes the banked rotation-dynamics
   question).

### Budget

9 runs (≤ max_runs 10), 73,700 training steps (≤ 75,000), 15,620 dense
steps (≤ 16,000). Phase A trains once and caches (columnar dense rows;
power as float32 tensors, ~5 MB); Phase B is CPU-only re-derivation.

### P2 probe (before Phase A; fills its Phase-A slot via `preloaded`)

Cell (8e-3, 1338) — cheapest cell with a guaranteed-deep committed
episode (0.478@1500). Stop conditions:

1. Coarse prefix bit-equal to the committed rows (mismatches == 0);
   any mismatch aborts the plan (substrate bug hunt, no full run).
2. Window [1100,2300] contains ≥1 interior dense episode with
   min_val < 0.5 (machinery check; guaranteed by cache if 1. holds).
3. Projected full Phase A ≤ 3 h wall-clock; else redesign.
4. Projected cache size ≤ 20 MB.

## Scope

Own committed grokked trajectories, toy scale (d=128, p=97), dense
re-observation only — no new training conditions. "Circuit" here means
the number-embedding Fourier structure (v1188's locus) specifically; the
attention/OV pathway is not measured. Every claim is about wd=1.0
post-grok dynamics of this substrate.
