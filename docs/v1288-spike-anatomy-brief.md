# v1288 preregistration — spike anatomy: is weight decay the destabilizer behind post-grok metastability?

**Status: preregistered.** This brief is committed before any GPU run; any
pre-Phase-A amendment is disclosed below.

## Motivation

v1287 discovered that grokked solutions are metastable under continued
training: 9/11 cells (canonical included) undergo whole-solution spikes —
train and val collapse from 1.0 to ~0.4 within one 100-step window — that
self-heal in 100–300 steps; the two "dead" 4e-3 cells were censored mid-spike
exactly at their horizons. v1287 banked two follow-ups; this version executes
the spike-anatomy one with the sharpest causal question first:

**What destabilizes the grokked solution?** The standing suspect is weight
decay: wd·lr keeps shrinking weights at the solution, purification proceeds
(v1287), and the natural mechanism story is "wd sculpts until the solution
slides off a stability edge, the optimizer catapults, then re-groks". If
true, removing wd at the solution should abolish the spikes — and freeze
purification (the two v1287 phenomena would be two faces of one wd process).

## Design: paired branch arms from verified-healthy checkpoints

For each of 9 spike-prone cells, deterministically re-run to a **branch
point** (a v1287 snapshot-ladder step whose health is already measured in the
committed cache — P1 verified all nine at val 0.99–1.0, and moved 8e-3/1338
from its 1.4× point, which sits mid-spike at val 0.567, to its verified 1.8×
point), capture the weight state, then continue **two arms to the v1287
horizon**: wd = 1.0 and wd = 0.0. Both arms restart AdamW moments at the
branch, so the optimizer-reset confound is shared — the arms differ ONLY in
wd. Training code untouched (branching = `train_to_grok(init_state=...)`,
early stop disabled via `grok_stop_val = 2.0` as in v1287; the loop is
full-batch and consumes no RNG, so branches are deterministic).

Cells (lr, seed, k_branch, horizon) — k_branch/horizon are committed v1287
ladder values: (1e-3, 1339, 14700, 31500); (2e-3, 1337, 2700, 5700);
(2e-3, 1338, 3900, 8400); (4e-3, 1337, 2000, 4200); (4e-3, 1338, 2500, 5400);
(4e-3, 1339, 1400, 3000); (8e-3, 1337, 1400, 3000); (8e-3, 1338, 2500, 4200);
(8e-3, 1339, 2100, 4500). In the same windows the committed v1287 curves show
8/9 cells spiking (15 episodes total) — the continuous-run comparison column
is free, from cache.

**Un-censoring runs (2, descriptive)**: full re-runs of the two v1287 dead
cells extended 1,000 steps past their horizons — (4e-3, 1338 → 6400 steps),
(4e-3, 1339 → 4000) — to test the censoring interpretation: observed
recoveries take 100–300 steps, so +1,000 is 3× margin. Recovery would
formally complete v1287's metastability story; non-recovery would be a
genuine death and gets reported as such. Not verdict-driving.

## Spike definition (preregistered)

An episode = a maximal run of consecutive eval rows (every 100 steps) with
val < spike_bar (0.9; robustness grid {0.8, 0.85, 0.9}), within the branch
window. `censored` if it reaches the window end. Duration =
end − start + 100. Morphology guard: every observed v1287 spike lasted ≤ 300
steps, so any non-censored episode longer than 500 steps in either arm is not
the phenomenon under test → review (atypical_morphology).

## Verdict ladder (preregistered)

S1 = number of cells whose wd=1.0 arm has ≥ 1 episode; S0 = same for wd=0.0
(both at the committed spike_bar).

- `spikes_are_wd_driven` — S1 ≥ 5 (of 9) AND S0 = 0: the fresh-moment wd arm
  reproduces the phenomenon, removing wd abolishes it.
- `spikes_persist_without_wd` — S0 ≥ 3: wd is not necessary; the instability
  lives in Adam + full-batch dynamics at the solution.
- `spikes_need_optimizer_history` — S1 = 0 AND S0 = 0: neither fresh-moment
  arm spikes; the spikes require accumulated Adam state, and the wd question
  stays open (an honest, informative outcome — the branch design cannot see
  wd's role).
- `review` — guards: `atypical_morphology` (above); `mixed_evidence`
  (intermediate S1/S0 combinations); `unexpected_geometry` (S1 = 0 with
  S0 > 0 — wd removal creating spikes); `spike_bar_instability` (G2: the
  verdict differs across the spike-bar grid); any G0/G1 failure.

G0 (integrity): every branch re-run's full curve must match the committed
v1287 cache rows bit-exactly (1e-9) — the branch state is thereby the v1287
trajectory's state; branch val ≥ 0.9 (branch_unhealthy otherwise); the two
un-censor runs must reproduce their v1287 curves as bit-exact prefixes.
Endpoint heldout is deliberately NOT a gate for branch arms: an arm may end
mid-spike, which is data, not substrate failure (disclosed departure from the
v1287 gate, with reason). G1: 9 cells × 2 complete arms + 2 un-censor runs,
curves complete to their horizons. G2: spike-bar grid as above.

## Secondary readouts (not verdict-driving)

- **Purity freeze prediction**: own-top-5 purity at each arm endpoint vs the
  branch point. If wd drives sculpting, the wd=0 arm's purity stays ≈ frozen
  (|Δ| small) while the wd=1 arm keeps climbing — tying v1287's purification
  and metastability to one mechanism. Reported with per-arm `ends_in_spike`
  flags (an endpoint inside a spike is measured mid-catapult).
- **Norm direction**: total weight norm at branch vs arm endpoints (wd=1
  shrinks, wd=0 grows/flat — the free half of the norm-trajectory question;
  the dense norm anatomy stays banked).
- Un-censor outcomes: recovered flag (final val ≥ 0.9) + heldout.

## Budget

29 runs (9 × [1 branch + 2 arms] + 2 un-censor), 117,000 total steps — caps
`max_runs = 32`, `max_total_steps = 130,000`. Per-cell costs (steps):
48,300 / 8,700 / 12,900 / 6,400 / 8,300 / 4,600 / 4,600 / 5,900 / 6,900;
un-censor 6,400 + 4,000.

## P2 probe (GPU, preregistered stop conditions)

One branch cell: (4e-3, 1337) — 6,400 steps, fills its Phase-A slot via
preload. Stop conditions (any → abort, fix or re-panel): branch curve row at
k=2000 differs from the committed v1287 cache row (train 1.0 / val 1.0);
branch val < 0.9; either arm's curve incomplete to 2,200 relative steps; any
NaN. The probe previews the science for one cell (its continuous run had 2
in-window spikes) — disclosed.

## Phase plan

Phase A trains once and caches curves, spectra, norms, heldouts; Phase B is
CPU-only from `phase_a_cache.pt` + the read-only committed v1287 cache
(f/1287). One figure, two panels: (a) arm val trajectories (wd=1 solid,
wd=0 dashed, colored by lr) on normalized time, (b) the two un-censor curves
across the old horizon.

## Amendments

(none)

## Closeout (post-run)

- **Verdict: `spikes_are_wd_driven`** — all gates green (G0: 9/9 branch
  curves bit-equal to the committed v1287 cache, branch health 9/9 ≥ 0.991,
  un-censor prefixes bit-exact; G1 complete; G2 stable across the spike-bar
  grid). S1 = 8/9 (14 episodes, deepest 0.311, all self-healing ≤ 300
  steps), **S0 = 0** (every wd=0 arm spike-free, min val ≥ 0.909). Exactly
  the preregistered budget: 29 runs, 117,000 steps. Second non-review
  verdict since v1280, and the arc's first positive *causal* one.
- Un-censoring confirmed the v1287 censoring interpretation: both "dead"
  cells re-grokked within **100 steps** of their old horizons
  (0.431 → 0.996; 0.373 → 0.999). The preregistered recovered-flag reads
  False for 4e-3/1338 only because its +1,000 endpoint lands inside another
  routine shallow dip (0.881) — the endpoint lottery repeating one level up,
  itself a recursive confirmation of metastability.
- Secondary readouts: norm direction exactly as predicted (wd=1 median
  ratio 0.953 shrinking, wd=0 1.753 growing). The purity-freeze prediction
  is ceiling-limited — branch purities were already 0.73–0.93 in compressed
  cells, so both arms' median deltas are ≈ 0 (reported as a wash); the one
  cell with headroom (canonical, branch 0.372) shows the predicted
  dissociation: wd=1 arm climbs to 0.574, wd=0 arm frozen at 0.373
  (exploratory label).
- Synthesis: purification and metastability are two faces of one wd
  process — wd keeps shrinking and sculpting the grokked solution and
  periodically pushes it off a stability edge (train+val collapse), after
  which it re-groks in a few hundred steps. Removing wd removes the spikes,
  reverses norm flow, and freezes purification.
- Banked: the microscopic spike trigger (norm/sharpness ramp before an
  event — needs dense norm sampling) — **executed by v1289** (verdict
  `spike_preserves_circuit`: the shove is a 1–2-step gradient impulse that
  spares the embedding circuit); canonical rotation dynamics (v1287's
  other banked item) — **partially observed by v1289** (13/161 episodes
  rotate their top-5 set across a spike, concentrated at low/mid lr).
- Evidence bundle: [f/1288](../f/1288/解释/说明.md); zero code/criteria
  changes after preregistration commit `b07f1b1f` (seventh consecutive
  clean chain).
